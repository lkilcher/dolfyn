function [ Data, Config, T_beam2xyz ] = signatureAD2CP_beam2xyz_enu( Data, Config, mode, twoZs )

if nargin == 3
	twoZs = 0;
end

ad2cpstr = 'AD2CP_';
ad2cpstr = '';

if strcmpi( mode, 'avg' )
	dataModeWord = 'Average';
	configModeWord = 'avg';
elseif strcmpi( mode, 'avg1' )
	dataModeWord = 'Alt_Average';
	configModeWord = 'avg1';
elseif strcmpi( mode, 'burst1' )
	dataModeWord = 'Alt_Burst';
	configModeWord = 'burst1';
elseif strcmpi( mode, 'burst' )
	dataModeWord = 'Burst';
	configModeWord = 'burst';
end

% make the assumption the beam mapping is the same for all measurements in a data file
activeBeams = Data.( [dataModeWord '_Physicalbeam'] )( 1, : );
activeBeams = activeBeams(find(activeBeams > 0));
numberOfBeams = length( activeBeams );
if numberOfBeams <= 2
	print( 'Transformations require at least 3 active beams.' )
	T_beam2xyz = nan;
	return
end


beam2xyz_vec = Config.([ad2cpstr configModeWord '_beam2xyz'] );
if numberOfBeams == 4,
    T_beam2xyz = [beam2xyz_vec(1:4); beam2xyz_vec(5:8); beam2xyz_vec(9:12); beam2xyz_vec(13:16)];
else
    if numberOfBeams == 3,
        T_beam2xyz = [beam2xyz_vec(1:3); beam2xyz_vec(4:6); beam2xyz_vec(7:9)];        
    end
end

% Special case
if strcmp(Config.instrumentName, 'Signature55kHz'),
    T_beam2xyz =[   1.9492   -0.9746   -0.9746; ...
             0   -1.6881    1.6881; ...
        0.3547    0.3547    0.3547];
end

if Config.fwVersionDoppler <= 2163 && numberOfBeams == 4,
    % Fix bug in transformation matrix in version 2163
    T_beam2xyz(2,:) = -T_beam2xyz(2,:);
end


disp(T_beam2xyz)
   
% verify we're not already in 'xyz'
if strcmpi( Config.( [ ad2cpstr configModeWord '_coordSystem' ] ), 'xyz' )
	disp( 'Velocity data is already in xyz coordinate system.' )
	return
end

xAllCells = zeros( length( Data.( [ dataModeWord '_TimeStamp' ] ) ), Config.( [ad2cpstr  configModeWord '_nCells' ] ) );
yAllCells = zeros( length( Data.( [ dataModeWord '_TimeStamp' ] ) ), Config.( [ad2cpstr  configModeWord '_nCells' ] ) );
zAllCells = zeros( length( Data.( [ dataModeWord '_TimeStamp' ] ) ), Config.( [ad2cpstr  configModeWord '_nCells' ] ) );
if twoZs == 1
	z2AllCells = zeros( length( Data.( [ dataModeWord '_TimeStamp' ] ) ), Config.( [ad2cpstr  configModeWord '_nCells' ] ) );
end

xyz = zeros( size( T_beam2xyz, 2 ), length( Data.( [ dataModeWord '_TimeStamp' ] ) ) );
beam = zeros( size( T_beam2xyz, 2 ), length( Data.( [ dataModeWord '_TimeStamp' ] ) ) );
for nCell = 1:Config.( [ad2cpstr  configModeWord '_nCells' ] )
	for i = 1:numberOfBeams
		beam( i, : ) = Data.( [ dataModeWord '_VelBeam' num2str( Data.( [ dataModeWord '_Physicalbeam' ] )( 1, i ) ) ] )( :, nCell )';
	end
	xyz = T_beam2xyz * beam;
	xAllCells( :, nCell ) = xyz( 1, : )';	
	yAllCells( :, nCell ) = xyz( 2, : )';
	zAllCells( :, nCell ) = xyz( 3, : )';
	if twoZs == 1
		z2AllCells( :, nCell ) = xyz( 4, : )';
	end
end

Config.( [ad2cpstr   configModeWord '_coordSystem' ] ) = 'xyz';
Data.( [ dataModeWord '_VelX' ] ) = xAllCells;
Data.( [ dataModeWord '_VelY' ] ) = yAllCells;

if twoZs == 1
	Data.( [ dataModeWord '_VelZ1' ] ) = zAllCells;
	Data.( [ dataModeWord '_VelZ2' ] ) = z2AllCells;
else
	Data.( [ dataModeWord '_VelZ' ] ) = zAllCells;
end





% verify we're not already in 'enu'
if strcmpi( Config.( [ad2cpstr   configModeWord '_coordSystem' ] ), 'enu' )
	disp( 'Velocity data is already in enu coordinate system.' )
	return
end

K = 3;
EAllCells = zeros( length( Data.( [dataModeWord  '_TimeStamp' ] ) ), Config.( [ad2cpstr   configModeWord '_nCells' ] ) );
NAllCells = zeros( length( Data.( [dataModeWord  '_TimeStamp' ] ) ), Config.( [ad2cpstr   configModeWord '_nCells' ] ) );
UAllCells = zeros( length( Data.( [dataModeWord  '_TimeStamp' ] ) ), Config.( [ad2cpstr   configModeWord '_nCells' ] ) );
if twoZs == 1
	U2AllCells = zeros( length( Data.( [dataModeWord  '_TimeStamp' ] ) ), Config.( [ad2cpstr  configModeWord '_nCells' ] ) );
   K = 4;
end

Name = ['X','Y','Z'];
ENU = zeros( K, Config.([ad2cpstr   configModeWord '_nCells' ]));
xyz = zeros( K, Config.([ad2cpstr   configModeWord '_nCells' ]));
for sampleIndex = 1:length(Data.( [dataModeWord  '_Error' ]));
   if (bitand(bitshift(uint32(Data.( [dataModeWord  '_Status' ])(sampleIndex)), -25),7) == 5)
      signXYZ=[1 -1 -1 -1];
   else
      signXYZ=[1 1 1 1];
   end

   hh = pi*(Data.([dataModeWord  '_Heading'])(sampleIndex)-90)/180;
   pp = pi*Data.([dataModeWord  '_Pitch'])(sampleIndex)/180;
   rr = pi*Data.([dataModeWord  '_Roll'])(sampleIndex)/180;

   % Make heading matrix
   H = [cos(hh) sin(hh) 0; -sin(hh) cos(hh) 0; 0 0 1];

   % Make tilt matrix
   P = [cos(pp) -sin(pp)*sin(rr) -cos(rr)*sin(pp);...
         0             cos(rr)          -sin(rr);  ...
         sin(pp) sin(rr)*cos(pp)  cos(pp)*cos(rr)];

   % Make resulting transformation matrix
   xyz2enu = H*P; 
   if (twoZs == 1)
      xyz2enu(1,3) = xyz2enu(1,3)/2;
      xyz2enu(1,4) = xyz2enu(1,3);
      xyz2enu(2,3) = xyz2enu(2,3)/2;
      xyz2enu(2,4) = xyz2enu(2,3);
      
      xyz2enu(4,:) = xyz2enu(3,:);
      xyz2enu(3,4) = 0;
      xyz2enu(4,4) = xyz2enu(3,3);
      xyz2enu(4,3) = 0;
   end

   for i = 1:K
      if (twoZs == 1) && (i >= 3)
         axs = [ Name(3) num2str((i-2),1) ];
      else
         axs = Name(i);
      end
      xyz( i, : ) = signXYZ(i) * Data.( [ dataModeWord '_Vel' axs] )( sampleIndex, : )';
   end
   ENU = xyz2enu * xyz;
   EAllCells( sampleIndex, : ) = ENU( 1, : )';	
   NAllCells( sampleIndex, : ) = ENU( 2, : )';
   UAllCells( sampleIndex, : ) = ENU( 3, : )';
      if twoZs == 1
      U2AllCells( sampleIndex, : ) = ENU( 4, : )';
      end
end
Config.( [ad2cpstr   configModeWord '_coordSystem' ] ) = 'enu';
Data.( [ dataModeWord '_VelEast' ] ) = EAllCells;
Data.( [ dataModeWord '_VelNorth' ] ) = NAllCells;
if twoZs == 1
	Data.( [ dataModeWord '_VelUp1' ] ) = UAllCells;
	Data.( [ dataModeWord '_VelUp2' ] ) = U2AllCells;
else
	Data.( [ dataModeWord '_VelUp' ] ) = UAllCells;
end



