# -*- coding: utf-8 -*-

for filename in ['log_20170521140359_RB-A','log_20170522063243_RB-A',\
                 'log_20170523040002_RB-A','log_20170524040001_RB-A',\
                 'log_20170525040002_RB-A','log_20170526040001_RB-A',\
                 'log_20170527040002_RB-A','log_20170528040001_RB-A',\
                 'log_20170529040001_RB-A','log_20170530040002_RB-A',\
                 'log_20170531040002_RB-A','log_20190512110952_RB-A',\
                 'log_20190512111451_RB-A','log_20190512111715_RB-A',\
                 'log_20190512111923_RB-A','log_20190512112200_RB-A',\
                 'log_20190512112608_RB-A','log_20190512113735_RB-A',\
                 'log_20190512131213_RB-A','log_20190512135710_RB-A',\
                 'log_20190512181850_RB-A','log_20190512221306_RB-A',\
                 'log_20190512222723_RB-A','log_20190513000837_RB-A',\
                 'log_20190513053112_RB-A','log_20190513113422_RB-A',\
                 'log_20190514153311_RB-A','log_20190514192003_RB-A',\
                 'log_20190519171923_RB-A','log_20190519185321_RB-A']:
    filenameIn = './log/'+filename+'.txt'
    # with codecs.open(filenameIn,'r',encoding='utf8') as f:
    with open(filenameIn, 'r', errors='ignore') as f:
        lines = f.read().splitlines()
    
    # process Unicode text
    filenameOut = './log/'+filename+'.txt'
    # with codecs.open(filenameOut,'a',encoding='utf8') as f:
    with open(filenameOut, 'w+', errors='ignore') as f:
        for line in lines:
            line = line.encode('latin1').decode('utf8', errors='ignore')
            f.write(line+'\n')