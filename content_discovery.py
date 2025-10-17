import subprocess
import time

def intel_content_discovery(file_path):

    try:
        wstart_time = time.time()
        print("waybackurls initiated....")
        cat_livesites1 = subprocess.Popen(["cat", "live_sites.txt"], stdout=subprocess.PIPE)
        waybackurls = subprocess.Popen(["waybackurls"], stdin=cat_livesites1.stdout, stdout=subprocess.PIPE)
        cat_livesites1.stdout.close()
        anew_urls = subprocess.Popen(["anew", "urls.txt"], stdin=waybackurls.stdout)
        waybackurls.stdout.close()
        
        # Wait for all processes to complete
        cat_livesites1.wait(timeout=100)
        waybackurls.wait(timeout=100)
        anew_urls.wait(timeout=100)
        
        wexecution_time = time.time() - wstart_time
        print(f"✅ waybackurls completed in {wexecution_time:.2f} seconds")
        # Check return codes
        if cat_livesites1.returncode != 0:
            raise subprocess.CalledProcessError(cat_livesites1.returncode, "cat")
        if waybackurls.returncode != 0:
            raise subprocess.CalledProcessError(waybackurls.returncode, "waybackurls")
        if anew_urls.returncode != 0:
            raise subprocess.CalledProcessError(anew_urls.returncode, "anew")
        
    except FileNotFoundError as e:
        print(f"❌ Command or file not found: {e}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Command '{e.cmd}' failed with exit code {e.returncode}")
    except PermissionError as e:
        print(f"❌ Permission denied: {e}")
    except OSError as e:
        print(f"❌ OS error: {e}")
    except subprocess.TimeoutExpired as e:
        print(f"❌ Process timed out: {e}")
    except KeyboardInterrupt:
        print(f"❌ Process interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")



    try:
        print("checking for live sites using httpx....")
        hstart_time = time.time()
        cat_urls = subprocess.Popen(["cat", "urls.txt"], stdout=subprocess.PIPE)
        grep_js = subprocess.Popen(["grep", r"\.js$"], stdin=cat_urls.stdout, stdout=subprocess.PIPE)
        cat_urls.stdout.close()
        httpx = subprocess.Popen(["httpx", "-silent", "-status-code", "200"], stdin=grep_js.stdout, stdout=subprocess.PIPE)
        grep_js.stdout.close()
        
        # Wait for processes to complete and get output
        httpx_output = httpx.communicate()[0]
        
        hexecution_time = time.time() - hstart_time
        print(f"✅ httpx completed in {hexecution_time:.2f} seconds")
        if httpx.returncode != 0:
            raise subprocess.CalledProcessError(httpx.returncode, "httpx")
        
        with open("live_js.txt", 'w') as f:
            f.write(httpx_output.decode())
        
    except FileNotFoundError as e:
        print(f"❌ Command or file not found: {e}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}: {e.cmd}")
    except PermissionError as e:
        print(f"❌ Permission denied: {e}")
    except IOError as e:
        print(f"❌ I/O error: {e}")
    except UnicodeDecodeError as e:
        print(f"❌ Encoding error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")



    
    try:
        print("Initiated katana....")
        kstart_time = time.time()
        cat_livesites2 = subprocess.Popen(["cat", "live_sites.txt"], stdout=subprocess.PIPE)
        katana = subprocess.Popen(["katana", "-jc", "-aff", "-d", "5", "-f", "qurl"], stdin=cat_livesites2.stdout, stdout=subprocess.PIPE)
        cat_livesites2.stdout.close()
        anew_katana_file = subprocess.Popen(["sort", "-u"], stdin=katana.stdout, stdout=open("katana_urls.txt", "w"))
        katana.stdout.close()
        
        # Wait for all processes to complete
        cat_livesites2.wait()
        katana.wait()
        anew_katana_file.wait()
        

        kexecution_time = time.time() -kstart_time
        print(f"✅ katana completed in {kexecution_time:.2f} seconds")
        # Check return codes
        if cat_livesites2.returncode != 0:
            raise subprocess.CalledProcessError(cat_livesites2.returncode, "cat")
        if katana.returncode != 0:
            raise subprocess.CalledProcessError(katana.returncode, "katana")
        if anew_katana_file.returncode != 0:
            raise subprocess.CalledProcessError(anew_katana_file.returncode, "sort")
        
    except FileNotFoundError as e:
        print(f"❌ Command or file not found: {e}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Command '{e.cmd}' failed with exit code {e.returncode}")
    except PermissionError as e:
        print(f"❌ Permission denied: {e}")
    except OSError as e:
        print(f"❌ OS error: {e}")
    except subprocess.TimeoutExpired as e:
        print(f"❌ Process timed out: {e}")
    except KeyboardInterrupt:
        print(f"❌ Process interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")





    try:
        # Arjun command with subprocess.Popen
        print("Initiated arjun1....")
        astart_time = time.time()
        arjun_command = [
            "arjun",
            "-i", "all_params_urls.txt",
            "-o", "arjun1_results.txt",
            "-t", "80",
            "--passive",
            "--disable-redirects", 
            "--timeout", "5",
            "--stable"
        ]
        
        # Run Arjun using Popen
        process = subprocess.Popen(
            arjun_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for process to complete with timeout
        stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout
        aexecution_time = time.time() -astart_time
        print(f"✅ httpx completed in {aexecution_time:.2f} seconds")
        # Check return code
        if process.returncode == 0:
            print("✅ Arjun completed successfully!")

            
        print("Initiated arjun2 for.....")
        a2start_time = time.time()
        open_urls = subprocess.Popen(["cat", "urls.txt"], stdout=subprocess.PIPE)
        grep_urls = subprocess.Popen(["grep", "?"], stdin=open_urls.stdout, stdout=subprocess.PIPE)
        open_urls.stdout.close()
        
        # Fixed: Use grep_urls.stdout instead of open_urls.stdout
        with open("params.txt", "w") as f:
            params = subprocess.Popen(["sort", "-u"], stdin=grep_urls.stdout, stdout=f)
        grep_urls.stdout.close()
        
        # Wait for the pipeline to complete
        params.wait()
        
        # Second Arjun command
        print("arjun2 initiated....")
        arjun2_command = [
            "arjun",
            "-i", "params.txt",
            "-o", "arjun2_results.txt",  # Changed output filename to avoid overwrite
            "-t", "80",
            "--passive",
            "--disable-redirects", 
            "--timeout", "5",
            "--stable"
        ]
        
        # Run second Arjun using Popen
        process2 = subprocess.Popen(
            arjun2_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout2, stderr2 = process2.communicate(timeout=300)
        a2execution_time = time.time() - a2start_time
        print(f"✅ Arjun completed in {a2execution_time:.2f} seconds")
        if process2.returncode == 0:
            print("✅ Second Arjun completed successfully!")

    except FileNotFoundError as e:
        print(f"❌ Command or file not found: {e}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}: {e.cmd}")
    except subprocess.TimeoutExpired as e:
        print(f"❌ Process timed out: {e}")
    except PermissionError as e:
        print(f"❌ Permission denied: {e}")
    except OSError as e:
        print(f"❌ OS error: {e}")
    except KeyboardInterrupt:
        print(f"❌ Process interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")



    #cat live_sites.txt | waybackurls | grep -E '\.js$' | httpx -silent > all_js.txt
    #cat all_js.txt katana_js.txt | sort -u | head -100 > quality_js.txt
    
    try:
        # Command 1: Get JS files from Wayback
        cmd1 = "cat urls.txt | grep -E '\\.js$' | httpx -silent > all_js.txt"
        waybackurls_js = subprocess.Popen(cmd1, shell=True)
        
        # Wait for first command to finish
        waybackurls_js.wait(timeout=300)  # 5 minute timeout
        
        # Check return code for first command
        if waybackurls_js.returncode != 0:
            raise subprocess.CalledProcessError(waybackurls_js.returncode, cmd1)
        
        # Command 2: Merge and filter
        cmd2 = "cat all_js.txt katana_urls.txt | sort -u | head -100 > quality_js.txt"
        katana_js = subprocess.Popen(cmd2, shell=True)
        katana_js.wait(timeout=300)  # 5 minute timeout
        
        # Check return code for second command
        if katana_js.returncode != 0:
            raise subprocess.CalledProcessError(katana_js.returncode, cmd2)
            
        print("✅ JS file discovery completed successfully!")

    except FileNotFoundError as e:
        print(f"❌ Command or file not found: {e}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
    except subprocess.TimeoutExpired as e:
        print(f"❌ Process timed out after 5 minutes: {e}")
    except PermissionError as e:
        print(f"❌ Permission denied: {e}")
    except OSError as e:
        print(f"❌ OS error: {e}")
    except KeyboardInterrupt:
        print(f"❌ Process interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    return