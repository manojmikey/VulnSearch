import re
import smart_reconnaissance
from pathlib import Path 
import content_discovery

#Validating user's domain....
def check_domain(domain):
    pattern = r'^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'

    if re.fullmatch(pattern,domain):
        print("Entered a valid domain....")
        return True
    else:
        raise ValueError(f"Invalid domain: {domain}. Example: 'example.com'")


def main():
    #Phase1: Smart Reconnaissance step
    try:
        
        domain_name = input("Enter the domain name you want to scan: ").strip()
        valid_domain = check_domain(domain_name)

        if(valid_domain):
            #Initiating the 1st phase...
            proceed = smart_reconnaissance.smart_reconn(domain_name)
            if proceed.success:
                print("Found the expected live sites, Check this file for manual testing: ",proceed.path)
                
            else:
                print("Failed: ",proceed)
    except Exception as e:
        print(e)
    
    #Phase2: Intelligent Content Discovrey step
    try:
        if not Path("live_sites.txt"):
            raise FileNotFoundError("Input file 'live_sites.txt' not found")
        content_discovery.intel_content_discovery("live_sites.txt")
        print("Phase 2:Content discovery is completed....")
        

    except FileNotFoundError as e:
        print(e)    
    except Exception as e:
        print(e)    



if __name__ == "__main__":
    main()