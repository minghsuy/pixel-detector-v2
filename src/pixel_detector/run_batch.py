import argparse
import asyncio
import csv
import os
from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import NoCredentialsError

from .batch_processor import BatchProcessor
from .logging_config import get_logger

logger = get_logger(__name__)


def parse_s3_path(s3_path):
    """Parses an S3 path into bucket and key."""
    if not s3_path.startswith("s3://"):
        raise ValueError("Invalid S3 path format")
    path_parts = s3_path.replace("s3://", "").split("/", 1)
    bucket = path_parts[0]
    key = path_parts[1] if len(path_parts) > 1 else ""
    return bucket, key


def upload_directory_to_s3(local_path, s3_bucket, s3_prefix):
    """Uploads a directory's contents to an S3 prefix."""
    s3 = boto3.client("s3")
    local_path = Path(local_path)
    for file_path in local_path.rglob("*"):
        if file_path.is_file():
            s3_key = f"{s3_prefix}/{file_path.relative_to(local_path)}"
            try:
                s3.upload_file(str(file_path), s3_bucket, s3_key)
                logger.info(f"Uploaded {file_path} to s3://{s3_bucket}/{s3_key}")
            except NoCredentialsError:
                logger.error("S3 credentials not found. Cannot upload results.")
                return
            except Exception as e:
                logger.error(f"Failed to upload {file_path} to S3: {e}")


def main():
    """
    Main function to run the batch processing of URLs from a CSV file.
    Supports both local and S3 paths for input and output.
    """
    parser = argparse.ArgumentParser(description="Batch process URLs for pixel detection.")
    parser.add_argument(
        "--input-file",
        type=str,
        required=True,
        help="Path to the input CSV file. Can be a local path or an S3 path (e.g., s3://my-bucket/input.csv).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/app/results",
        help="Directory to save the output results. Can be a local path or an S3 path (e.g., s3://my-bucket/results/).",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Number of concurrent scans to run.",
    )
    parser.add_argument(
        "--batch-id",
        type=str,
        default=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        help="A unique identifier for this batch run.",
    )
    args = parser.parse_args()

    logger.info(f"Starting batch process with ID: {args.batch_id}")
    logger.info(f"Input file: {args.input_file}")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Concurrency level: {args.concurrency}")

    local_input_file = args.input_file
    is_s3_output = args.output_dir.startswith("s3://")

    # Handle S3 input file
    if args.input_file.startswith("s3://"):
        logger.info(f"Downloading input file from S3: {args.input_file}")
        try:
            s3 = boto3.client("s3")
            bucket, key = parse_s3_path(args.input_file)
            file_name = Path(key).name
            # Using /tmp for downloaded files in container environments
            os.makedirs("/tmp/input", exist_ok=True)
            local_input_file = f"/tmp/input/{file_name}"
            s3.download_file(bucket, key, local_input_file)
            logger.info(f"Successfully downloaded to {local_input_file}")
        except NoCredentialsError:
            logger.error("S3 credentials not found. Please configure them (e.g., via IAM role).")
            return
        except Exception as e:
            logger.error(f"Failed to download from S3: {e}", exc_info=True)
            return

    # Use a local directory for processing, even for S3 output
    local_output_dir = f"/tmp/results/{args.batch_id}" if is_s3_output else args.output_dir
    Path(local_output_dir).mkdir(parents=True, exist_ok=True)

    # Read domains from CSV
    try:
        with open(local_input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if 'url' not in reader.fieldnames:
                logger.error(f"Input CSV file '{local_input_file}' must have a 'url' column.")
                return
            domains = [row['url'] for row in reader]
    except FileNotFoundError:
        logger.error(f"Input file not found: {local_input_file}")
        return
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}", exc_info=True)
        return

    if not domains:
        logger.warning("Input file is empty. No domains to process.")
        return

    logger.info(f"Loaded {len(domains)} domains to process.")

    # Prepare and run the batch processor
    processor = BatchProcessor(
        max_concurrent=args.concurrency,
        checkpoint_dir=str(Path(local_output_dir) / "checkpoints"),
    )

    try:
        asyncio.run(
            processor.process_batch(
                domains=domains,
                output_dir=local_output_dir,
                batch_id=args.batch_id,
            )
        )
        logger.info("Batch processing completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred during batch processing: {e}", exc_info=True)

    # After processing, upload results if output is S3
    if is_s3_output:
        logger.info(f"Uploading results to S3: {args.output_dir}")
        try:
            bucket, prefix = parse_s3_path(args.output_dir)
            upload_directory_to_s3(local_output_dir, bucket, prefix)
            logger.info("S3 upload complete.")
        except Exception as e:
            logger.error(f"Failed to upload results to S3: {e}", exc_info=True)


if __name__ == "__main__":
    main()
