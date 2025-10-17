import subprocess
from pathlib import Path
import time


#After the successful completion of subdomain enumeration by subfinder and amass....
def proceed():

    try:    
        #Combining the outputed files....
        print("Combining files...")
        result = subprocess.run(
            ["cat", "subfinder.txt", "amass.txt"],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            text = True
        )
        if result.returncode == 0:
            with open("all_subs.txt",'w')as f:
                f.write(result.stdout)
        print("Combining files completed....")
    except result.stderr as e:
        print(e)
    
    try:
        print("Initiating dnsx....")
        dstart_time = time.time()
        dnsx_command = f"dnsx -l all_subs.txt - resp -silent"
        dcommand = dnsx_command.split()
         
         #Enumeration by dnsx....
        dnsx_result = subprocess.run(
            dcommand,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            text = True
        )
        dexecution_time = time.time() - dstart_time
        print(f"✅ dnsx completed in {dexecution_time:.2f} seconds")
        
        #Checking the status of dnsx command...
        if dnsx_result.returncode == 0:
            print("Success..... copying into a file")
            #Copying results in to the file....
            with open("resolved_subs.txt",'w')as f:
                f.write(dnsx_result.stdout)
        

    except subprocess.TimeoutExpired:
        print("Ping timed out!")
    except FileNotFoundError:
        print("dnsx not found. Is it installed?")
    except Exception as e:
        print("Unexpected error has occured: ",e)
        
    if not Path("resolved_subs.txt") or Path("resolved_subs.txt").stat().st_size == 0:
        print("Error Occured for dnsx copying a file...")
        code ={
            'success':False,
            'path':[]
            }
        return code
    
    try:
        print("Initiating httpx....")
        hstart_time = time.time()
        httpx_command = f"httpx -list resolved_sub.txt -silent -title -status-code -tech-detect"
        hcommand = httpx_command.split()
        
        #Enumeration by httpx....
        httpx_result = subprocess.run(
            hcommand,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            text = True
        )
        hexecution_time = time.time() - hstart_time
        print(f"✅ httpx completed in {hexecution_time:.2f} seconds")

        #Checking the status of httpx command...
        if httpx_result.returncode == 0:
            print("Success.... copying into a file")
            #Copying results in to the file....
            with open("live_sites.txt",'w')as f:
                f.write(httpx_result.stdout)

    except subprocess.TimeoutExpired:
        print("Ping timed out!")
    except FileNotFoundError:
        print("httpx not found. Is it installed?")
    except Exception as e:
        print("Unexpected error has occured: ",e)
    
    
    live_sites_path = []
    if not Path("resolved_subs.txt") or Path("resolved_subs.txt").stat().st_size == 0:
        print("Error Occured for dnsx copying a file...")
        code2 ={
            'success':False,
            'path':[]
            }
        return code2
    else:
        live_sites_path.append(Path("resolved_subs.txt"))
    
    return {'success':True,'path':live_sites_path}




 
#This is the 1st initial step...
def smart_reconn(domain):
    try:
        print("Initiating subfinder....")
        start_time = time.time()
        subfinder_command = f"subfinder -d {domain} -silent -all"
        command = subfinder_command.split()
        #Subdomain enumeration by subfinder....
        result_subfinder = subprocess.run(
            command,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            text = True,
            timeout=300
        )
        execution_time = time.time() - start_time
        print(f"✅ Subfinder completed in {execution_time:.2f} seconds")
        
        #Checking the status of subfinder command...
        if result_subfinder.returncode == 0:
            print("subfindder_finished copying to a file")
            #Copying output in to a file....
            with open("subfinder.txt",'w')as f:
                f.write(result_subfinder.stdout)

    except subprocess.TimeoutExpired:
        print("Ping timed out!")
    except FileNotFoundError:
        print("Subfinder not found. Is it installed?")
    except Exception as e:
        print("Unexpected error has occured: ",e)

    try:
        print("Initiating amass....")
        astart_time = time.time()
        amass_command = f"assetfinder --subs-only {domain}"
        acommand = amass_command.split()
        #subdomain enumeration by amass....
        result_amass =  subprocess.run(
            acommand,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            text = True,
            timeout = 600
        )
        aexecution_time = time.time() - astart_time
        print(f"✅ amass completed in {aexecution_time:.2f} seconds")
        #Checking the status of amass command....
        if result_amass.returncode == 0:
            print("amass_finished copying into a file")
            #Copying results into a file....
            with open("amass.txt",'w')as f:
                f.write(result_amass.stdout)

    except subprocess.TimeoutExpired:
        print("Ping timed out!")
    except FileNotFoundError:
        print("amass not found. Is it installed?")
    except Exception as e:
        print("Unexpected error has occured: ",e)

    paths = []
    #Checking whether the files exists or not as output of subfinder and amass commands...
    subfinder_path = Path("subfinder.txt")
    amass_path = Path("amass.txt")
    
    check = False
    if subfinder_path.exists() and subfinder_path.stat().st_size>0:
        print("yess")
        check = True
        paths.append(subfinder_path)
    if amass_path.exists() and amass_path.stat().st_size>0:
        print("yesa")
        check = True
        paths.append(amass_path)
    if not subfinder_path.exists() and not amass_path.exists():
        print("No")
        return {'success':False,'path':[]}
    
    if check:
        for path in paths:
            print("Check out this files for manual testing",path)
        return proceed()
   
    return {'success':False,'path':[]}





