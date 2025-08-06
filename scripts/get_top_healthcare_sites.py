#!/usr/bin/env python3
"""
Gather top healthcare websites from various public sources for testing.
This creates a test list before running the full 15K scan.
"""
import json
import requests
from pathlib import Path

def get_healthcare_test_sites():
    """
    Curated list of major healthcare websites for testing.
    Based on public information about top healthcare providers.
    """
    
    # Major healthcare systems and hospitals
    healthcare_sites = [
        # Government health sites
        "nih.gov",
        "cdc.gov",
        "medicare.gov",
        "medicaid.gov",
        "healthcare.gov",
        "hhs.gov",
        "fda.gov",
        "va.gov",
        
        # Major hospital systems (from the Semrush screenshot)
        "clevelandclinic.org",
        "mayoclinic.org",
        "hopkinsmedicine.org",
        "uclahealth.org",
        "nyp.org",
        "sutterhealth.org",
        "kaiserpermanente.org",
        "providence.org",
        "dignityhealth.org",
        "adventhealth.com",
        "baptisthealth.com",
        "beaumont.org",
        "nm.org",  # Northwestern Medicine
        "cedars-sinai.org",
        "mskcc.org",  # Memorial Sloan Kettering
        "mdanderson.org",
        "stanfordhealthcare.org",
        "massgeneral.org",
        "brighamandwomens.org",
        "childrenshospital.org",
        
        # Health information sites
        "webmd.com",
        "healthline.com",
        "drugs.com",
        "rxlist.com",
        "medscape.com",
        "ncbi.nlm.nih.gov",
        "uptodate.com",
        
        # Insurance companies
        "uhc.com",
        "anthem.com",
        "cigna.com",
        "humana.com",
        "bcbs.com",
        "aetna.com",
        "molina.com",
        
        # Pharmacy chains
        "walgreens.com",
        "cvs.com",
        "riteaid.com",
        "kroger.com",
        
        # Medical device companies
        "medtronic.com",
        "jnj.com",
        "abbott.com",
        "bd.com",
        
        # Telehealth
        "teladoc.com",
        "amwell.com",
        "mdlive.com",
        "doctorondemand.com",
        
        # Regional health systems
        "nyulangone.org",
        "mountsinai.org",
        "pennmedicine.org",
        "ucsfhealth.org",
        "uchicagomedicine.org",
        "vanderbilthealth.com",
        "dukehealth.org",
        "uhhospitals.org",
        "ohiohealth.com",
        "spectrumhealth.org",
        "froedtert.com",
        "sanfordhealth.org",
        "intermountainhealthcare.org",
        "sharp.com",
        "scripps.org",
        "memorialhermann.org",
        "bswhealth.com",
        "methodisthealth.com",
        "piedmont.org",
        "wellstar.org",
        "orlandohealth.com",
        "baycare.org",
        "henryford.com",
        "osfhealthcare.org",
        "unitypoint.org",
        "allina.com",
        "healthpartners.com",
        "parkview.com",
        "sentara.com",
        "inova.org",
        "christushealth.org",
        "commonspirit.org",
        "trihealth.com",
        "rush.edu",
        "lumc.edu",
        
        # Additional from screenshot
        "athenahealth.com",
        "aarp.org",
        
        # Mental health
        "psychologytoday.com",
        "betterhelp.com",
        "headspace.com",
        
        # Medical journals/education
        "nejm.org",
        "jamanetwork.com",
        "thelancet.com",
        "nature.com/nm",
        
        # Patient portals/EMR
        "mychart.com",
        "followmyhealth.com",
        "nextmd.com"
    ]
    
    return healthcare_sites[:100]  # Return exactly 100 sites

def create_test_file(output_file="healthcare_test_100.txt"):
    """Create a test file with 100 healthcare websites"""
    sites = get_healthcare_test_sites()
    
    # Write to file
    with open(output_file, 'w') as f:
        for site in sites:
            f.write(f"{site}\n")
    
    print(f"✅ Created {output_file} with {len(sites)} healthcare websites for testing")
    
    # Also create a smaller quick test file
    quick_test = sites[:10]
    with open("healthcare_quick_test.txt", 'w') as f:
        for site in quick_test:
            f.write(f"{site}\n")
    
    print(f"✅ Also created healthcare_quick_test.txt with 10 sites for quick testing")
    
    return sites

def verify_domains(domains_file="healthcare_test_100.txt"):
    """Quick verification that domains look valid"""
    with open(domains_file, 'r') as f:
        domains = [line.strip() for line in f if line.strip()]
    
    print(f"\n📊 Domain Statistics:")
    print(f"Total domains: {len(domains)}")
    
    # Count by TLD
    tlds = {}
    for domain in domains:
        tld = domain.split('.')[-1]
        tlds[tld] = tlds.get(tld, 0) + 1
    
    print("\nTop Level Domains:")
    for tld, count in sorted(tlds.items(), key=lambda x: x[1], reverse=True):
        print(f"  .{tld}: {count}")
    
    print("\nFirst 10 domains:")
    for i, domain in enumerate(domains[:10], 1):
        print(f"  {i}. {domain}")

if __name__ == "__main__":
    # Create the test files
    create_test_file()
    
    # Verify the results
    verify_domains()
    
    print("\n🚀 Ready to test! Run:")
    print("   docker run ... pixel-scanner:safe batch /app/input/healthcare_test_100.txt -o /app/results")
    print("\nFor quick 10-site test:")
    print("   docker run ... pixel-scanner:safe batch /app/input/healthcare_quick_test.txt -o /app/results")