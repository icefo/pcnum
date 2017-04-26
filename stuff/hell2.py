from collections import OrderedDict

default_decklink_to_raw = OrderedDict()
default_decklink_to_raw['part1'] = ('nice', '-n', '0', 'ffmpeg', '-y', '-nostdin', '-f', 'decklink', '-i')
default_decklink_to_raw['input'] = ["Intensity Pro (1)@16", ]
default_decklink_to_raw['recording_duration'] = ['-t', '60', ]  # in seconds
default_decklink_to_raw['part2'] = ('-acodec', 'copy', '-vcodec', 'copy')
default_decklink_to_raw['frame_rate'] = ['-r', '25', ]
default_decklink_to_raw['output'] = ['/this/is/a/path/video_file.mkv', ]

default_raw_to_h264_aac = OrderedDict()
default_raw_to_h264_aac['part1'] = ('nice', '-n', '11', 'ffmpeg', '-y', '-nostdin', '-i')
default_raw_to_h264_aac['input'] = ['/this/is/a/path/video_file.mkv', ]
default_raw_to_h264_aac['aspect_ratio'] = ['-aspect', '4:3']
default_raw_to_h264_aac['part2'] = (
'-c:v', 'libx264', '-crf', '25', '-preset', 'slow', '-filter:v', 'hqdn3d=3:2:2:3',
'-c:a', 'libfdk_aac', '-vbr', '3')
default_raw_to_h264_aac['output'] = ['/this/is/a/path/video_file.mkv', ]

a = ""
for value in default_decklink_to_raw.values():
    for b in value:
        a = a + " " + b

print(a)
