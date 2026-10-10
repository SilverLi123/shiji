#include <libproc.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
int main(int argc,char **argv){
 if(argc<3)return 1;int seconds=atoi(argv[1]);
 struct timespec stamp;clock_gettime(CLOCK_MONOTONIC,&stamp);unsigned long long startNs=(unsigned long long)stamp.tv_sec*1000000000+stamp.tv_nsec;
 for(int t=0;t<=seconds;t++){
  clock_gettime(CLOCK_MONOTONIC,&stamp);unsigned long long elapsedNs=(unsigned long long)stamp.tv_sec*1000000000+stamp.tv_nsec-startNs;
  for(int i=2;i<argc;i++){int pid=atoi(argv[i]);struct rusage_info_v4 info={0};char path[PROC_PIDPATHINFO_MAXSIZE]={0};
   if(proc_pid_rusage(pid,RUSAGE_INFO_V4,(rusage_info_t*)&info)!=0||proc_pidpath(pid,path,sizeof(path))<=0)return 2;
   printf("{\"second\":%d,\"elapsedNs\":%llu,\"pid\":%d,\"userNs\":%llu,\"systemNs\":%llu,\"footprint\":%llu,\"resident\":%llu,\"path\":\"%s\"}\n",t,elapsedNs,pid,info.ri_user_time,info.ri_system_time,info.ri_phys_footprint,info.ri_resident_size,path);
  }fflush(stdout);if(t<seconds)sleep(1);
 }return 0;
}
