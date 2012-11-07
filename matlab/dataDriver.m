% This program when run will suck up the ProcessTraces parameters into a
% Structure and add the entry into the database.
% Parameters will turn on various functionality.
% Read about function getfield, setfield, rmfield, isfield,

clear all
close all
loadtools;
addpath ../sac
addpath functions
addpath([userdir,'/programming/matlab/jsonlab'])
%% Variables
sacfolder = '/media/TerraS/CN';
databasedir = '/media/TerraS/database';
pfile = 'stack_P.sac';
sfile = 'stack_S.sac';
%%  Select Station to Process and load station data
method = 'kanamori';
station = '';
%{

ALRB
B1NU
BMBC
CLSB
COQB
EDM
FLLB
HNB
HOPB
KASO
LDIO
LLLB
MEDA
MUMO
NSKO
PINU
PRDA
RAMB
RLKO
SBNU
SLEB
SULB
TALB
THMB
UBRB
WALA
WAPA


%}
dbfile = fullfile(databasedir, [station,'.mat'] );
workingdir = fullfile(sacfolder,station);
clear db dbold
if exist(dbfile, 'file')
    load(dbfile)
    dbold = db;
    display(dbold.processnotes)
end

%% Run ToolChain
ProcessTraces

%% Assign Data
if ~exist('db', 'var')
    db = struct();
end
[ db ] = assigndb( db, method, station, brec(:,1:round(45/dt)), ...
    pslow, dt, npb, fLow, fHigh, results, boot);

%% Plot the results if we completed the processing
close all
plotStack(db, method);

if strcmp(method, 'bostock')
    fprintf('Vp is %f +/- %1.3f \n',db.mb.vbest, db.mb.stdVp )
    fprintf('R is %f +/- %1.3f \n',db.mb.rbest, db.mb.stdR )
    fprintf('H is %f +/- %1.3f \n',db.mb.hbest, db.mb.stdH )
    if exist('dbold','var')
        if isfield(dbold,'mb')
            fprintf('Old MB Vp is %f +/- %1.3f \n',dbold.mb.vbest, dbold.mb.stdVp )
            fprintf('Old MB R is %f +/- %1.3f \n',dbold.mb.rbest, dbold.mb.stdR )
            fprintf('Old MB H is %f +/- %1.3f \n',dbold.mb.hbest, dbold.mb.stdH )
        end
        if isfield(dbold,'hk')
            fprintf('Old hk R is %f +/- %1.3f \n',dbold.hk.rbest, dbold.hk.stdR )
            fprintf('Old hk H is %f +/- %1.3f \n',dbold.hk.hbest, dbold.hk.stdH )
        end
    end
end

if strcmp(method, 'kanamori')
    fprintf('R is %f +/- %1.3f \n',db.hk.rbest, db.hk.stdR )
    fprintf('H is %f +/- %1.3f \n',db.hk.hbest, db.hk.stdH )
    if exist('dbold','var')
        if isfield(dbold,'hk')
            fprintf('Old hk R is %f +/- %1.3f \n',dbold.hk.rbest, dbold.hk.stdR )
            fprintf('Old hk H is %f +/- %1.3f \n',dbold.hk.hbest, dbold.hk.stdH )
        end
        if isfield(dbold,'mb')
            fprintf('Old MB R is %f +/- %1.3f \n',dbold.mb.rbest, dbold.mb.stdR )
            fprintf('Old MB H is %f +/- %1.3f \n',dbold.mb.hbest, dbold.mb.stdH )
            fprintf('Old MB Vp is %f +/- %1.3f \n',dbold.mb.vbest, dbold.mb.stdVp )
        end
    end
end

%% Enter Finishing commands:
notes = input('Enter Processing Notes: ', 's');
db.processnotes = notes;
% Enter use / ignore flag
db.usable = input('Enter 1 to set as usable or 0 to set as unusable: ');
% Save entrydbold.mb.
saveit = input('Save data to .mat file? (y|n): ','s');
switch lower(saveit)
    case 'y'
        save(dbfile,'db') % Save .mat file with bulk data
        fprintf('Saved data\n')
    otherwise
        fprintf('Warning: data not saved\n')
end

close all