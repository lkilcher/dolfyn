cdef struct Header:
    unsigned char  sync
    unsigned char  hdrSize
    unsigned char  ID
    unsigned char  family
    unsigned short dataSize
    unsigned short dataChecksum
    unsigned short hdrChecksum


# ctypedef struct t_DataSetDescription4Bit:
#     unsigned short beamData1 : 4
#     unsigned short beamData2 : 4
#     unsigned short beamData3 : 4
#     unsigned short beamData4 : 4

# cdef struct t_status:
#     unsigned long _empty1 : 1
#     unsigned long bdScaling : 1
#     unsigned long _empty2 : 1
#     unsigned long _empty3 : 1
#     unsigned long _empty4 : 1
#     unsigned long echoFreqBin : 5
#     unsigned long boostRunning : 1
#     unsigned long telemetryData : 1
#     unsigned long echoIndex : 4
#     unsigned long activeConfiguration : 1
#     unsigned long lastMeasLowVoltageSkip : 1
#     unsigned long prevWakeUpState : 4
#     unsigned long autoOrient : 3
#     unsigned long orientation : 3
#     unsigned long wakeupstate : 4

# cdef struct t_status0:
#     unsigned short procIdle3 : 1
#     unsigned short procIdle6 : 1
#     unsigned short procIdle12 : 1
#     unsigned short _empty1 : 12
#     unsigned short stat0inUse : 1
    
cdef struct BurstHead:
    unsigned char  version
    unsigned char  offsetOfData
    short headconfig
    # struct headconfig:
    #     unsigned short pressure: 1
    #     unsigned short temp: 1
    #     unsigned short compass: 1
    #     unsigned short tilt: 1
    #     unsigned short _empty: 1
    #     unsigned short velIncluded : 1
    #     unsigned short ampIncluded : 1
    #     unsigned short corrIncluded : 1
    #     unsigned short altiIncluded : 1
    #     unsigned short altiRawIncluded : 1
    #     unsigned short ASTIncluded : 1
    #     unsigned short EchoIncluded : 1
    #     unsigned short ahrsIncluded : 1
    #     unsigned short PGoodIncluded : 1
    #     unsigned short stdDevIncluded : 1
    #     unsigned short _unused : 1
    unsigned long  serialNumber;
    unsigned char  year;
    unsigned char  month;
    unsigned char  day;
    unsigned char  hour;
    unsigned char  minute;
    unsigned char  seconds;
    unsigned short microSeconds100;
    unsigned short soundSpeed     # resolution: 0.1 m/s
    short          temperature    # resolution: 0.01 degree C
    unsigned long  pressure
    unsigned short heading
    short          pitch
    short          roll
    short beamconfig
    # bit 15-12: Number of beams, bit 11-10: coordinate system, bit 9-0: number of cells
    # OR number of echo sounder cells (echosounder mode)
    unsigned short cellSize
    unsigned short blanking
    unsigned char  nominalCorrelation
    unsigned char  pressTemp
    unsigned short battery
    short          magnHxHyHz[3]
    short          accl3D[3]
    unsigned short ambVelocity # OR echoFrequency (echosounder mode)
    short DataSetDescription4bit
    unsigned short transmitEnergy
    char           velocityScaling
    char           powerlevel
    short          magnTemperature
    short          rtcTemperature
    unsigned short error
    unsigned short status0       # Unsigned short
    unsigned long status        # Unsigned long
    unsigned long  ensembleCounter
    # Then the *data* starts...
   
# cdef struct BotTrackHead:
#     unsigned char  version
#     unsigned char  offsetOfData
#     struct headconfig:
#         unsigned short pressure: 1
#         unsigned short temp: 1
#         unsigned short compass: 1
#         unsigned short tilt: 1
#         unsigned short _empty: 1
#         unsigned short velIncluded : 1
#         unsigned short _unused1 : 1
#         unsigned short _unused2 : 1
#         unsigned short distIncluded : 1
#         unsigned short fomIncluded : 1
#         unsigned short _unused3 : 6
#     unsigned long  serialNumber
#     unsigned char  year
#     unsigned char  month
#     unsigned char  day
#     unsigned char  hour
#     unsigned char  minute
#     unsigned char  seconds
#     unsigned short microSeconds100
#     unsigned short soundSpeed
#     short          temperature  # Celsius
#     unsigned long  pressure
#     unsigned short heading
#     short          pitch
#     short          roll
#     unsigned short beams_cy # bit 11-10: coordinate system, bit 15-12: number of beams
#     unsigned short cellSize
#     unsigned short blanking
#     unsigned short velocityRange
#     unsigned short battery
#     short magnHxHyHz[3]
#     short accl3D[3]
#     unsigned int ambVelocity
#     t_bottom
    
# cdef struct BurstHead_old:
#     unsigned char ver
#     unsigned char DataOffset
#     unsigned short config
#     unsigned int SerialNum
#     unsigned char year
#     unsigned char month
#     unsigned char day
#     unsigned char hour
#     unsigned char minute
#     unsigned char second
#     unsigned short usec100
#     unsigned short c_sound
#     signed short temp
#     signed int pressure
#     unsigned short heading
#     unsigned short pitch
#     unsigned short roll
#     unsigned short HeadConfig
#     unsigned short CellSize
#     unsigned short Blanking
#     unsigned char NomCorr
#     unsigned char TempPress
#     unsigned short Voltage
#     unsigned short MagX
#     unsigned short MagY
#     unsigned short MagZ
#     unsigned short AccX
#     unsigned short AccY
#     unsigned short AccZ
#     unsigned short AmbigVel
#     unsigned short DataDescription
#     unsigned short TransmitEnergy
#     signed char VelScale
#     signed char PowerLevel
#     signed short TempMag
#     signed short TempClock
#     unsigned short Error
#     unsigned short Status0
#     unsigned int Status
#     unsigned int ens
