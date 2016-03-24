#include <TrueRandom.h>
#include <SoftReset.h>
#include <avr/wdt.h>
#include "math.h"
#include <DS3232RTC.h>
#include <Time.h>
#include <Wire.h>

#define wandering 0xF1
#define pokeInM 0xF2
#define pokeOutM 0xF3
#define pokeInL 0xF4
#define pokeOutL 0xF5
#define pokeInR 0xF6
#define pokeOutR 0xF7
#define rewardStart 0xF8
#define rewardEnd 0xF9
#define waitToSignalStop 0xF0

//Arduino pin configuration
int pin_flasherL = 6;
int pin_flasherM = 7;
int pin_flasherR = 8;
int pin_laser = 9;
int pin_reward = 4;
int pin_stop_signal = 5;
int pin_photobeamL = A0;
int pin_photobeamM = A1;
int pin_photobeamR = A2;
int pin_power = 12;


//Experimental Configuration
int threshold_for_photobeam = 500;
long LH = 1536; //1500ms*1.024
long t;
long baudrate = 115200;
long time_tick;

// Some useful helper functions.

// interrupt service ruitine
// This ruitine was registered to count time tick at 1024hz.

void isr(){
  time_tick++;
}

long newMillis(){
  return time_tick;
}

//Random Generator: Generate a length of N random numbers sorted sequence from a given range.

int *generateStopTrialNum(int stopArray[], int startN, int endN, int N){
  /* Function to generate N random numbers between startN (inclusive) and endN (exlusive).
     endN must be bigger than endN.
  */
  int vals[endN-startN];
   
  for (int i=0; i<endN-startN;i++)
    vals[i]=i+startN;
    
  for (int i=0; i<N;i++)
  {
    int r = TrueRandom.random(i, endN-startN);    // select from a decreasing set
    stopArray[i]=vals[r];
    swap(vals, r, i);     // switch the chosen one with the last of the selection set.
  }
  //for (int i=0; i<N; i++)
  //  stopArray[i] = vals[i];

  
  for (int i=0;i<N;i++){
    for(int j=0;j<N-i-1;j++){
      if(stopArray[j]>stopArray[j+1]){
        int temp=stopArray[j];
        stopArray[j]=stopArray[j+1];
        stopArray[j+1]=temp;
      }
    }
  }
  return stopArray;
 }
 
// Helper function: swap two values in an array
void swap(int *vals, int a, int b)
{
  int t = vals[a];
  vals[a] = vals[b];
  vals[b] = t;
}
// Helper function: check if the current trial is stop trial
/*
bool checkIfStop(int trialNum, int *stopTrials, int imin, int imax)
{
  //imin is the first index usually 0; imax is the size of stopTrials - 1
  if(imin>imax){
    return false;
  }else{
    int mid=(-imin+imax)/2+imin;
    if(trialNum>stopTrials[mid]){
      return checkIfStop(trialNum, stopTrials, mid+1, imax);
    }else if(trialNum<stopTrials[mid]){
      return checkIfStop(trialNum, stopTrials, imin, mid-1);
    }else{
      return true;
    }
  }
}
*/
bool checkIfStop(long t, int k)
{
  // 20ms timeout
  while(newMillis()-t<100){
    if(Serial.available()){
      char isStop=Serial.read();
      if(isStop=='n'){
        return false;
      }else if(isStop=='s'){
        return true; 
      }
    }
  }
  writeData("check stop timeout",k);
  return false;
}

// Output data to Serial for communication with python
void writeData(const char str[], long t){
  Serial.print(str);
  Serial.print(',');
  Serial.println(t);
  Serial.flush();
}

void writeCorrectStop(char side='l'){
  if(side=='l'){
    writeData("IL",0);
    writeData("OL",0);
  }else{
    writeData("IR",0);
    writeData("OR",0);
  }
}

void writeGoError(char side='l'){
  writeData("Go Error",0);
  if(side=='l'){
    writeData("IL",0);
    writeData("OL",0);
  }else{
    writeData("IR",0);
    writeData("OR",0);
  }
  writeData("OM",0);
  writeData("RS",0);
}

void writeStopError(char side='l'){
  writeData("Stop Error",0);
  if(side=='l'){
    writeData("OL",0);
  }else{
    writeData("OR",0);
  }
  writeData("IM",0);
  writeData("OM",0);
  writeData("RS",0);
}

void writeLHError(char side='l'){
  writeData("LH Error",0);
  if(side=='l'){
    writeData("IL",0);
    writeData("OL",0);
  }else{
    writeData("IR",0);
    writeData("OR",0);
  }
  writeData("IM",0);
  writeData("OM",0);
  writeData("RS",0);
}

//Flash light object
class Flasher
{
  public:
    int ledpin;
    bool isON;
    int state;
    int interval;
    long onMillis;
    Flasher(int pin)
    {
      ledpin = pin;
      pinMode(ledpin, OUTPUT);
      isON = false;
      state = LOW;
      onMillis=0;
    }
    void setParams(int freq)
    {
      interval = 1024/freq;
    }
    void on()
    {
      state=HIGH;
      digitalWrite(ledpin, state);
      isON = true;
      onMillis=newMillis();
    }
    void off()
    {
      state=LOW;
      digitalWrite(ledpin, state);
      isON = false;
    }
    void updateState(long t)
    {
      if(isON){
         if(t-onMillis>interval){
           onMillis=t;
           state=!state;
           digitalWrite(ledpin,state);
         }
      } 
    }
    int getPin()
    {
      return ledpin;
    }
    bool isOn()
    {
      return isON;
    }
};


// add Laser Class used for Optogenetics
class Laser
{
  public:
    int laserpin;
    bool isON;
    int state;
    int interval;
    long onMillis;
    long laserStartMillis;
    long duration; 
    Laser(int pin)
    {
      laserpin = pin;
      pinMode(laserpin, OUTPUT);
      isON = false;
      state = LOW;
      onMillis=0;
      laserStartMillis=0;
    }
    void setParams(int freq, long dur)
    {
      // dur: millisecond
      interval = 1024/freq;
      duration = dur;
    }
    void start()
    {
      state=HIGH;
      digitalWrite(laserpin, state);
      isON=true;
      laserStartMillis=newMillis();
    }
    
    void on()
    {
      state=HIGH;
      digitalWrite(laserpin, state);
      isON = true;
      onMillis=newMillis();
    }
    void off()
    {
      state=LOW;
      digitalWrite(laserpin, state);
      isON = false;
    }
    void updateState(long t)
    {
      if(t-laserStartMillis<duration){
        if(isON){
           if(t-onMillis>interval){
             onMillis=t;
             state=!state;
             digitalWrite(laserpin,state);
           }
        } 
      }else{
        off();
      }
    }
    
    int getPin()
    {
      return laserpin;
    }
    bool isOn()
    {
      return isON;
    }
};



//PhotoBeam object
class PhotoBeam
{
  public:
    int beampin;
    int threshold;
    PhotoBeam(int pin, int th)
    {
      beampin = pin;
      threshold = th;
    }
    bool isInterrupted()
    {
      return analogRead(beampin) > threshold;
    }
    int getVoltage()
    {
      return analogRead(beampin);
    }
    int getPin()
    {
      return beampin;
    }
};

//Reward object
class RewardValve
{
  public:
    int rewardpin;
    long rewardVolume;
    long rewardStartTime;
    // long rewardEndTime;
    bool rewardOn;
    RewardValve(int pin)
    {
      rewardpin = pin;
      pinMode(rewardpin, OUTPUT);
      rewardOn = false;
    }
    void setParams(long reward){
      rewardVolume=reward;
    }
    void on()
    {
      if (!rewardOn)
      {
        rewardOn = true;
        digitalWrite(rewardpin, HIGH);
        rewardStartTime = newMillis();
      }
    }
    void off()
    {
      if (rewardOn)
      {
        rewardOn = false;
        digitalWrite(rewardpin, LOW);
        //rewardEndTime = newMillis();
      }
    }
     long getRewardVolume()
    {
      return rewardVolume;
    }
     long getRewardStartTime()
    {
      return rewardStartTime;
    }

    bool isRewarding()
    {
      return rewardOn;
    }
};
// Stop signal object
class StopSignal
{
  public:
  int stoppin;
  int duration;
  
  StopSignal(int pin, int time1)
  {
    stoppin=pin;
    duration=time1;
  }
  void on(int f=4000)
  {
    tone(stoppin, f, duration);
  }
}; 
  
  

class ExperimentalProcedure
{
  protected:
  int ex_status;
  bool delayOn;
  bool errorDelayOn;
  long delayOnTime;
  long errorDelayOnTime;
  long requiredDelay;
  long requiredErrorDelay;
  public:
  ExperimentalProcedure(long rDelay=5120, long eDelay=5120)
  {
    ex_status=wandering;
    delayOn = false;
    delayOnTime = 0;
    requiredDelay = rDelay;
    errorDelayOn = false;
    errorDelayOnTime=0;
    requiredErrorDelay=eDelay;
  }  
  virtual void updating(long t){};  
};


// Instantiations of hardwares
Flasher f[3]={
  Flasher(pin_flasherL),
  Flasher(pin_flasherM),
  Flasher(pin_flasherR)
};
PhotoBeam pb[3]={
  PhotoBeam(pin_photobeamL, threshold_for_photobeam),
  PhotoBeam(pin_photobeamM, threshold_for_photobeam),
  PhotoBeam(pin_photobeamR, threshold_for_photobeam)
};

RewardValve reward(pin_reward);

StopSignal stopS(pin_stop_signal, 100);

Laser laser(pin_laser);


class Stage1:public ExperimentalProcedure
{
  int trialNum;
  public:
  Stage1():ExperimentalProcedure(){
    trialNum=0;
  }
  void setParams(long rdelay){
    requiredDelay=rdelay;
  }
  
  void updating(long t){
    if (reward.isRewarding())
    {
    if (t - reward.getRewardStartTime() >= reward.getRewardVolume())
      reward.off();
    }
    if (delayOn)
    {
    if (t - delayOnTime >= requiredDelay)
      delayOn = false;
    }else{
    f[1].updateState(t);
    switch (ex_status) {
      case wandering:
        ex_status = pokeInM;
        f[1].on();
        trialNum+=1;
        writeData("trialNum",trialNum);
        break;
      case pokeInM:
        if (pb[1].isInterrupted())
        {
          ex_status = pokeOutM;
          reward.on();
          f[1].off();
          writeData("IM",t);
        }
        break;
      case pokeOutM:
        if (!pb[1].isInterrupted())
        {
          ex_status = wandering;
          delayOn = true;
          delayOnTime = newMillis();
          writeData("OM",t);
        }
        break;
      }
    }
  }
};


class Stage2:public ExperimentalProcedure
{
  //side flasher
  Flasher *sf;
  Flasher *fm;
  //side photobeam
  PhotoBeam *spb;
  int trialNum;
  
  public:
  Stage2():ExperimentalProcedure(){}
  void setParams(char side='l'){
    fm=&f[1];
    trialNum=0;
    if(side=='l')
    {
      sf = &f[0];
      spb = &pb[0];
    }else{
      sf = &f[2];
      spb = &pb[2];
    }
  }

  void updating(long t)
  {
    if (reward.isRewarding())
    {
      if (t - reward.getRewardStartTime() >= reward.getRewardVolume())
        reward.off();
    }
    sf->updateState(t);
    fm->updateState(t);
    switch(ex_status){
      case wandering:
        ex_status=pokeInL;
        sf->on();
        trialNum+=1;
        writeData("trialNum",trialNum);
        break;
      case pokeInL:
        if(spb->isInterrupted()){
          ex_status=pokeOutL;
          sf->off();
          f[1].on();
          reward.on();
        }
        break;
      case pokeOutL:
        if(!spb->isInterrupted())
          ex_status=pokeInM;
        break;
      case pokeInM:
        if(pb[1].isInterrupted()){
          ex_status=pokeOutM;
          f[1].off();
          writeData("IM",t);
        }
        break;
      case pokeOutM:
        if(!pb[1].isInterrupted()){
          ex_status=wandering;
          writeData("OM",t);
        }
        break;
    }
  }
};


class Stage3:public ExperimentalProcedure
{
  //side flasher
  Flasher *fl;
  Flasher *fm;
  Flasher *fr;
  //side photobeam
  PhotoBeam *pbl;
  PhotoBeam *pbm;
  PhotoBeam *pbr;
  //Limited Hold
  bool lh;
  char side;
  long limitedHold;
  long lhStartTime;
  int trialNum;
  public:
  Stage3():ExperimentalProcedure(){}
  void setParams(long limitHold, char s='l'){
    limitedHold = limitHold;
    side = s;
    lh = false;
    lhStartTime=0;
    trialNum=0;
    if(side=='l')
    {
      fl = &f[0];
      fm = &f[1];
      fr = &f[2];
      pbl = &pb[0];
      pbm = &pb[1];
      pbr = &pb[2];
    }else{
      fl = &f[2];
      fm = &f[1];
      fr = &f[0];
      pbl = &pb[2];
      pbm = &pb[1];
      pbr = &pb[0];
    }
  }

  void updating(long t)
  {
    if (reward.isRewarding())
    {
      if (t - reward.getRewardStartTime() >= reward.getRewardVolume())
        reward.off();
    }
    if(lh){
      if(t-lhStartTime>limitedHold)
        lh=false;
    }    
    fm->updateState(t);
    fr->updateState(t);
    fl->updateState(t);
    switch(ex_status){
      case wandering:
        ex_status=pokeInR;
        if(fm->isOn())
          fm->off();
        if(fl->isOn())
          fl->off();
        fr->on();
        trialNum+=1;
        writeData("trialNum",trialNum);
        break;
      case pokeInR:
        if(pbr->isInterrupted()){
          ex_status=pokeOutR;
          fr->off();
          fl->on();
          if(side=='l')
            writeData("IR",t);
          else
            writeData("IL",t);
        }
        break;
      case pokeOutR:
        if(!pbr->isInterrupted()){
          ex_status=pokeInL;
          lh=true;
          lhStartTime=t;
          if(side=='l')
            writeData("OR",t);
          else
            writeData("OL",t);
        }
        break;
      case pokeInL:
        if(lh && pbl->isInterrupted()){
          ex_status=pokeOutL;
          fl->off();
          fm->on();
          reward.on();
          if(side=='l')
            writeData("IL",t);  //output timestamp
          else
            writeData("IR",t);
          writeData("RS",t);
        }else if(lh && pbm->isInterrupted()){
          ex_status=wandering;
          fl->off();
          writeData("IM",t);
          writeGoError(side);
        }else if(!lh){
          ex_status=wandering;
          fl->off();
          writeLHError(side);
        }
        break;
      case pokeOutL:
        if(!pbl->isInterrupted()){
          ex_status=pokeInM;
          if(side=='l')  
            writeData("OL",t);
          else
            writeData("OR",t);
        }
        break;
      case pokeInM:
        if(pbm->isInterrupted()){
          ex_status=pokeOutM;
          fm->off();
          writeData("IM",t);
        }
        break;
      case pokeOutM:
        if(!pbm->isInterrupted()){
          ex_status=wandering;
          writeData("OM",t);
        }
        break;
    }
  }
};

class Stage4:public ExperimentalProcedure
{
  //side flasher
  Flasher *fl;
  Flasher *fm;
  Flasher *fr;
  //side photobeam
  PhotoBeam *pbl;
  PhotoBeam *pbm;
  PhotoBeam *pbr;
  //stop signal
  StopSignal *stopSignal;
  
  bool lh;   //Limited Hold
  char side;
  bool isStopTrial;
  bool stopChecked;
  long limitedHold;
  long lhStartTime;
  int trialNum;
  int sessionLength;  //total trial number (320 trials usually)
  int baselineLength; //baseline trial number (20 trials usually)
  int stopTrialsNum;  // the number of stop trials in the total trials.
  
  public:
  Stage4():ExperimentalProcedure(){}
  void setParams(long limitHold, char s='l', int sessionNumber=320, int baselineNumber=20, int stopTrialsNumber=60, long rdelay=5000){
    limitedHold = limitHold;
    side=s;
    lh = false;
    isStopTrial=false;
    stopChecked=false;
    lhStartTime=0;
    trialNum = 0;
    sessionLength = sessionNumber;
    baselineLength = baselineNumber;
    stopTrialsNum = stopTrialsNumber;
    requiredDelay=rdelay;
    stopSignal=&stopS;
    if(side=='l')
    {
      fl = &f[0];
      fm = &f[1];
      fr = &f[2];
      pbl = &pb[0];
      pbm = &pb[1];
      pbr = &pb[2];
    }else{
      fl = &f[2];
      fm = &f[1];
      fr = &f[0];
      pbl = &pb[2];
      pbm = &pb[1];
      pbr = &pb[0];
    }
  }
    
  void updating(long t)
  {
    if(reward.isRewarding())
    {
      if (t - reward.getRewardStartTime() >= reward.getRewardVolume()){
        reward.off();
        //writeData("rewardEnd",t);
      }
    }
    if(lh){
      if(t-lhStartTime>limitedHold)
        lh=false;
    }
    if (delayOn)
    {
    if (t - delayOnTime >= requiredDelay)
      delayOn = false;
    }else{
      fm->updateState(t);
      fr->updateState(t);
      fl->updateState(t);
      switch(ex_status){
        case wandering:
          ex_status=pokeInR;
          if(fm->isOn())
            fm->off();
          if(fl->isOn())
            fl->off();
          fr->on();
          trialNum++;
          writeData("trialNum",trialNum);
          if(trialNum>baselineLength){
            stopChecked=false;
            isStopTrial = checkIfStop(t, trialNum);
            if(isStopTrial){
              writeData("TT",2);
            }else{
              writeData("TT",1);
            }
          }else{
            writeData("TT",1);
          }
          break;
        case pokeInR:
          if(pbr->isInterrupted()){
            ex_status=pokeOutR;
            fr->off();
            fl->on();
            if(side=='l')
              writeData("IR",t);
            else
              writeData("IL",t);
          }
          break;
        case pokeOutR:
          if(!pbr->isInterrupted()){
            if(!isStopTrial){
              ex_status=pokeInL;
              lh=true;
              lhStartTime=t;
            }else if(isStopTrial){
              ex_status=pokeInM;
              stopSignal->on();
              fl->off();
              fm->on();
              writeData("SS",t);
            }
            if(side=='l')
              writeData("OR",t);
            else
              writeData("OL",t);
          }
          break;
        case pokeInL:
          if(lh && pbl->isInterrupted()){
            ex_status=pokeOutL;
            fl->off();
            fm->on();
            if(side=='l')
              writeData("IL",t);  //output timestamp
            else
              writeData("IR",t);
          }else if(lh && pbm->isInterrupted()){
            ex_status=wandering;
            fl->off();
            delayOn=true;
            delayOnTime=t;
            writeData("IM",t);
            writeGoError(side);
          }else if(!lh){
            ex_status=wandering;
            fl->off();
            delayOn=true;
            delayOnTime=t;
            writeLHError(side);
          }
          break;
        case pokeOutL:
          if(!pbl->isInterrupted()){
            ex_status=pokeInM;
            if(side=='l')  
              writeData("OL",t);
            else
              writeData("OR",t);
          }
          break;
        case pokeInM:
          if(pbm->isInterrupted()){       
            ex_status=pokeOutM;
            fm->off();
            reward.on();
            writeData("IM",t);
            writeData("RS",t);
            if(isStopTrial)
              writeCorrectStop(side);
          }else if(isStopTrial && pbl->isInterrupted()){
            ex_status=wandering;
            fm->off();
            delayOn=true;
            delayOnTime=t;
            if(side=='l')
              writeData("IL",t);
            else
              writeData("IR",t);
            writeStopError(side);
          }
          break;
        case pokeOutM:
          if(!pbm->isInterrupted()){
            ex_status=wandering;
            writeData("OM",t);
          }
          break;
      }
    }
  }
};




class Test:public ExperimentalProcedure
{
  //side flasher
  Flasher *fl;
  Flasher *fm;
  Flasher *fr;
  //side photobeam
  PhotoBeam *pbl;
  PhotoBeam *pbm;
  PhotoBeam *pbr;
  //stop signal
  StopSignal *stopSignal;
  
  bool lh;   //Limited Hold
  char side;
  bool isStopTrial;
  bool stopChecked;
  long limitedHold;
  long lhStartTime;
  long stopDelayOnTime;
  bool stopDelayOn;
  bool stopSkipped;
  int trialNum;
  int sessionLength;  //total trial number (320 trials usually)
  int baselineLength; //baseline trial number (20 trials usually)
  int stopTrialsNum;  // the number of stop trials in the total trials.
  int blockLength;
  int blockNumber;
  bool isLaserOn;
  int ssd; // Stop signal delay
  bool ssdCatched;
  String initialSSD;
  
  public:
  Test():ExperimentalProcedure(){}
  void setParams(long limitHold, char s='l', int sessionNumber=320, int baselineNumber=20, int stopTrialsNumber=60, long rdelay=5000, int blockL=100, int blockN=3, int isLaser=0){
    limitedHold = limitHold;
    side=s;
    lh = false;
    isStopTrial=false;
    stopChecked=false;
    lhStartTime=0;
    stopDelayOnTime=0;
    stopDelayOn=false;
    stopSkipped=false;
    trialNum = 0;
    ssd=0;
    ssdCatched=false;
    initialSSD="";
    sessionLength = sessionNumber;
    baselineLength = baselineNumber;
    stopTrialsNum = stopTrialsNumber;
    blockLength = blockL;
    blockNumber = blockN;
    if(isLaser==1){
      isLaserOn=true;
    }else{
      isLaserOn=false;
    }
    requiredDelay=rdelay;
    stopSignal=&stopS;
    if(side=='l')
    {
      fl = &f[0];
      fm = &f[1];
      fr = &f[2];
      pbl = &pb[0];
      pbm = &pb[1];
      pbr = &pb[2];
    }else{
      fl = &f[2];
      fm = &f[1];
      fr = &f[0];
      pbl = &pb[2];
      pbm = &pb[1];
      pbr = &pb[0];
    }
  }
    
  void updating(long t)
  {
    if(reward.isRewarding())
    {
      if (t - reward.getRewardStartTime() >= reward.getRewardVolume()){
        reward.off();
        //writeData("rewardEnd",t);
      }
    }
    // obtain the initial stop signal delay ssd when baseline ended from the control program in PC.
    while(trialNum==baselineLength+1 && !ssdCatched){
       while(Serial.available()){
         char inByte=Serial.read();
           if(inByte==','){
             ssdCatched=true;
           }else{
             initialSSD+=inByte;
           }
       }
       if(ssdCatched){
         ssd=initialSSD.toInt();
         writeData("ssd",ssd);
       }
    }
    // check limit hold
    if(lh){
      if(t-lhStartTime>limitedHold)
        lh=false;
    }
    // check to play stop signal
    if(stopDelayOn){
      if(t-stopDelayOnTime>=ssd){
        stopSignal->on();
        stopDelayOn=false;
        writeData("SS",t);
        writeData("SSD",ssd);
      }
    }
    // start status-checking loop
    if (delayOn)
    {
    if (t - delayOnTime >= requiredDelay)
      delayOn = false;
    }else{
      fm->updateState(t);
      fr->updateState(t);
      fl->updateState(t);
      switch(ex_status){
        case wandering:
          ex_status=pokeInR;
          if(fm->isOn())
            fm->off();
          if(fl->isOn())
            fl->off();
          fr->on();
          trialNum++;
          writeData("trialNum",trialNum);
          // check if stop
          if(trialNum>baselineLength){
            stopChecked=false;
            isStopTrial = checkIfStop(t,trialNum);
            if(isStopTrial){
              writeData("TT",2);
            }else{
              writeData("TT",1);
            }
          }else{
            writeData("TT",1);
          }
          break;
        case pokeInR:
          if(pbr->isInterrupted()){
            ex_status=pokeOutR;
            fr->off();
            fl->on();
            if(side=='l')
              writeData("IR",t);
            else
              writeData("IL",t);
          }
          break;
        case pokeOutR:
          if(!pbr->isInterrupted()){
            if(!isStopTrial){
              ex_status=pokeInL;
              lh=true;
              lhStartTime=t;
            }else if(isStopTrial){
              ex_status=waitToSignalStop;
              stopDelayOnTime=t;
              stopDelayOn=true;
              //fl->off();
              //fm->on();
            }
            if(side=='l')
              writeData("OR",t);
            else
              writeData("OL",t);
          }
          break;
        case waitToSignalStop:
          if(!stopDelayOn){
            ex_status=pokeInM;
            fl->off();
            fm->on();
          }else if(stopDelayOn && pbl->isInterrupted()){
            ex_status=pokeOutL;
            stopDelayOn=false;
            stopSkipped=true;
            if(ssd>50)
              ssd-=50;
            else
              ssd=0;
            fl->off();
            fm->on();
            writeData("TS",trialNum);
            if(side=='l')
              writeData("IL",t);  //output timestamp
            else
              writeData("IR",t);
          }else if(stopDelayOn && pbm->isInterrupted()){
            ex_status=wandering;
            stopDelayOn=false;
            fl->off();
            delayOn=true;
            delayOnTime=t;
            writeData("TS",trialNum);
            writeData("IM",t);
            writeGoError(side);
          }
          break;
        case pokeInL:
          if(lh && pbl->isInterrupted()){
            ex_status=pokeOutL;
            fl->off();
            fm->on();
            if(side=='l')
              writeData("IL",t);  //output timestamp
            else
              writeData("IR",t);
          }else if(lh && pbm->isInterrupted()){
            ex_status=wandering;
            fl->off();
            delayOn=true;
            delayOnTime=t;
            writeData("IM",t);
            writeGoError(side);
          }else if(!lh){
            ex_status=wandering;
            fl->off();
            delayOn=true;
            delayOnTime=t;
            writeLHError(side);
          }
          break;
        case pokeOutL:
          if(!pbl->isInterrupted()){
            ex_status=pokeInM;
            if(side=='l')  
              writeData("OL",t);
            else
              writeData("OR",t);
          }
          break;
        case pokeInM:
          if(pbm->isInterrupted()){       
            ex_status=pokeOutM;
            fm->off();
            reward.on();
            if(isStopTrial && !stopSkipped){
              writeCorrectStop(side);
              ssd+=50;
            }else if(isStopTrial && stopSkipped){
              stopSkipped=false;
            }
            writeData("IM",t);
            writeData("RS",t);
          }else if(isStopTrial && pbl->isInterrupted()){
            if(!stopSkipped){
              ex_status=wandering;
              if(ssd>50)
                ssd-=50;
              else
                ssd=0;
              fm->off();
              delayOn=true;
              delayOnTime=t-requiredDelay+1024;  //stop error delay is 1 second
              writeData("ssd",-50);
              if(side=='l')
                writeData("IL",t);
              else
                writeData("IR",t);
              writeStopError(side);
            }else{
              ex_status=pokeInM;
            }
          }
          break;
        case pokeOutM:
          if(!pbm->isInterrupted()){
            ex_status=wandering;
            writeData("OM",t);
          }
          break;
      }
    }
  }
};


class TestBox:public ExperimentalProcedure
{
  public:
  TestBox():ExperimentalProcedure(){}
  void setParams(long rdelay){
    requiredDelay=rdelay;
  }
  
  void updating(long t){
    if(Serial.available()){
      char inByte = Serial.read();
      if(inByte=='t'){
        reward.on();
      }else if(inByte=='s'){
        reward.off();
      }else if(inByte=='f'){
        stopS.on();
      }
    }      
  }
};




int stage;
char side;
long lh;
int len;
int stopNum;
int baseline;
long rdelay;
long reward_volume;
int blockLength;
int blockNumber;
int blinkFreq;
int isLaser;
int laserFreq;
long laserDur;

String inputArguments[14];
String singleArgument="";
int counter=0;
boolean argumentsComplete = false;

void getParams() {
  while (Serial.available()) {
    // get the new byte:
    char inByte = Serial.read(); 
    if(inByte==','){
      inputArguments[counter]=singleArgument;
      singleArgument = "";
      counter++;
    }
    // if the incoming character is a newline, set a flag
    // so the main loop can do something about it:
    else if (inByte == '\n') {
      argumentsComplete = true;
    }
    // add it to the inputString:
    else{
      singleArgument += inByte;
    }
  }
}


ExperimentalProcedure * ep;
Stage1 s1;
Stage2 s2;
Stage3 s3;
Stage4 s4;
Test test;
TestBox tb;

void setup()
{
  Serial.begin(baudrate);
 
  while(!argumentsComplete){
    getParams();
  }
  
  stage=inputArguments[0].toInt();
  side = char(inputArguments[1][0]);
  lh=inputArguments[2].toInt();
  len=inputArguments[3].toInt();
  baseline=inputArguments[4].toInt();
  stopNum=inputArguments[5].toInt();
  rdelay=inputArguments[6].toInt();
  blockLength=inputArguments[7].toInt();
  blockNumber=inputArguments[8].toInt();
  
  reward_volume=inputArguments[9].toInt();
  reward.setParams(reward_volume); 
  
  blinkFreq=inputArguments[10].toInt();
  f[0].setParams(blinkFreq);
  f[1].setParams(blinkFreq);
  f[2].setParams(blinkFreq);

  isLaser=inputArguments[11].toInt();
  laserFreq=inputArguments[12].toInt();
  laserDur=inputArguments[13].toInt();
  laser.setParams(laserFreq, laserDur);
  
  if(stage==1){
    s1.setParams(rdelay);
    ep=&s1;
  }else if(stage==2){
    s2.setParams(side);
    ep=&s2;
  }else if(stage==3){
    s3.setParams(lh, side);
    ep=&s3;
  }else if(stage==4){
    s4.setParams(lh, side, len, baseline, stopNum,rdelay);
    ep=&s4;
  }else if(stage==5){
    test.setParams(lh, side, len, baseline, stopNum,rdelay, blockLength, blockNumber, isLaser);
    ep=&test;
  }else if(stage==6){
    ep=&tb;
  }else{
    Serial.println("Wrong Arguments!,0");
  } 
  Serial.println("Session Start,0");
  // attach interrupt to DS3231 square wave output 
  // This gives a much more accurate time count  1s=1024 ticks
  RTC.squareWave(SQWAVE_1024_HZ);
  time_tick=0;
  attachInterrupt(1, isr, RISING);
}

void loop()
{
  t = newMillis();
  ep->updating(t);
  if(Serial.available()){
    char command = Serial.read();
    if(command=='r'){
      soft_restart();
    }
  }
  /*
  Serial.println(pb[0].getVoltage());
  Serial.println(pb[1].getVoltage());
  Serial.println(pb[2].getVoltage());
  Serial.println();
  delay(100);*/
}



