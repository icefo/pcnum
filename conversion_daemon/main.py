import subprocess


def run_process(shell_command):
    process = subprocess.Popen(shell_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    while True:
        if process.poll() is not None:  # returns None while subprocess is running
            break

        stdout_line = process.stdout.readline()[:-5]
        if stdout_line.startswith("frame="):
            list_of_characters = []
            counter = 0
            for character in stdout_line:
                if not character == " ":
                    list_of_characters.append(character)
                elif not stdout_line[counter - 1] == "=" and not stdout_line[counter - 1] == " ":
                    list_of_characters.append(character)
                counter += 1

            # ffmpeg_output example : frame=17 fps=0.0 q=0.0 size=1kB time=00:00:00.34 bitrate=18.0kbits/s
            ffmpeg_output = "".join(list_of_characters)
            stdout_dictionary = {}
            for key_value in ffmpeg_output.split(" "):
                a = key_value.split("=")
                stdout_dictionary[a[0]] = a[1]
            # {'fps': '0.0', 'bitrate': '18.0kbits/s', 'frame': '16', 'time': '00:00:00.34', 'q': '0.0', 'size': '1kB'}
            yield stdout_dictionary

command = [
            'nice', '-n', '19',
                'ffmpeg',
                    '-i', '/home/adrien/Documents/tm/output2min.mkv',
                        '-strict', '-2',
                        '-t', '10',
                        '-c:v', 'libx264', '-crf', '26', '-preset', 'slow', '-filter:v', 'hqdn3d=3:2:2:3',
                        '-c:a', 'aac', '-b:a', '128k',
                    '/home/adrien/Documents/tm/output2min_lossy.mkv'
            ]


for line in run_process(command):
    print(line)

# The last line give the final size of the file (audio + video + mux)
# {'time': '00:00:10.00', 'bitrate': '2771.4kbits/s', 'fps': '8.0', 'q': '-1.0', 'Lsize': '3385kB', 'frame': '250'}
# use Variable bitrate for the conversion!!!