listo = ['nice',
 '-n',
 '19',
 'ffmpeg',
 '-i',
 '/home/adrien/Vidéos/AMERICAN_GANGSTER/title00.mkv',
 '-t',
 '10',
 '-c:v',
 'libx264',
 '-crf',
 '18',
 '-preset',
 'medium',
 '-filter:v',
 'hqdn3d=3:2:2:3',
 '-c:a',
 'libfdk_aac',
 '-b:a',
 '192k',
 '/home/adrien/documents/tm/american gansters -- 2001']
a = ""
for i in listo:
    a = a + i + " "
print(a)