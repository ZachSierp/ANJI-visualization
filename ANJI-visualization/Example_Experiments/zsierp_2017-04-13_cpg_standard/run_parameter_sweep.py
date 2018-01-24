# Import the os module, for the os.walk function
import os
import sys
import time
from time import gmtime, strftime

def sh( command):
  output = subprocess.check_output( command , shell=True).decode("utf-8")
  return output.strip().split("\n")

bigred2=os.path.isdir( "/N/dc2/scratch/" )

strftime("%Y-%m-%d %H:%M:%S", gmtime())
exp_name=""

#bigred2 only
lock_directory="/N/dc2/scratch/jasoyode/LOCK"


if len(sys.argv) < 3:
  print("You need to specify an exp directory (first) and name (second)!")
  quit()
else:
  exp_dir=sys.argv[1]
  exp_name=sys.argv[2]
  print( "Experiment directory: {} \nExperiment name: {}".format(exp_dir, exp_name) )

 
# Set the directory you want to start from
rootDir = "{}/{}".format( exp_dir, 'JOBS_DIR/')

for dirName, subdirList, fileList in os.walk(rootDir):
  print('Found directory: {}'.format(dirName) )
  
  
  for fname in sorted(fileList):
    print('Found job file: {}'.format(fname) )
    
    job_name=  fname.replace(".properties","")
    full_file= "{}/DATA_DIR/{}/run/run0.xml".format(exp_dir, job_name )
    full_folder = "{}/DATA_DIR/{}/run/".format(exp_dir, job_name )
    
    #### LOCK UNTIL RELEASED##################
    if bigred2:
      os.system("{}/get_lock.sh".format(lock_directory) )
    ##########################################
    
    #this is a weak but functional semaphore, really needs to be some kind of delay to guarantee it though
    if os.path.isfile( full_file  ):
      print("{} already exists, it is not guaranteed to be complete though!".format( full_file) )
    else:
      os.system("mkdir -p {}".format( full_folder ))
      os.system("touch {}".format(full_file) )
      
      #### RELEASE LOCK NOW THAT WE CREATED DIRECTORY######
      if bigred2:
        os.system("{}/release_lock.sh".format(lock_directory) )
      #####################################################
      
      start = time.time()
      current_time= strftime("%Y-%m-%d %H:%M:%S", gmtime() )
      os.system("echo \"{} started at {}\" >> {}/log_jobs.txt".format(fname, current_time, exp_dir))
      
      #os.system("cd ../../JARS && nice -n10 java -jar ExperimentBuilder_Evolver.jar {}/JOBS_DIR/{}".format(exp_dir, fname))
      os.system("cd ../../JARS && nice -n10 java -jar TargetSequence_Evolver.jar {}/JOBS_DIR/{}".format(exp_dir, fname))
      
      current_time= strftime("%Y-%m-%d %H:%M:%S", gmtime() )
      os.system("cd {}".format( exp_dir ) )
      os.system("echo \"{} completed at {}\" >> {}/log_jobs.txt".format(fname, current_time, exp_dir ))
      time_taken= time.time() - start
      os.system("echo \"{} took {} seconds\" >> {}/completed_jobs.txt".format(fname, time_taken, exp_dir ))
      
    #### RELEASE LOCK AFTER EACH ITERATION##############
    if bigred2:
      os.system("{}/release_lock.sh".format(lock_directory) )
    #### LOCK UNTIL RELEASED#############################

  print('Completed directory: {}'.format(dirName) )
  