a = ['nice', '-n', '0', 'ffmpeg', '-y', '-nostdin', '-f', 'decklink', '-i', '-format_code', 'pal', '-video_input', 'composite', '-i', 'Intensity Pro (1)', '-t', '60', '-acodec', 'copy', '-vcodec', 'copy', '/media/storage/raw/asdfsd -- 1900 -- 72429a01-e489-46fb-8481-1e03754203d4.nut']
s = ""
for b in a:
    s = s + " " + b

print(s)