

def parse(path):
    f = open(path)
    print(type(f))
    lines = f.readlines()
    print(len(lines))
    larr = lines[3].split(';')
    print(larr[4])
    print(larr)
    with open('errors_{}.txt'.format(1234), 'w') as the_file:

        for line in lines:
            line_arr = line.split(';')
            # print(len(line_arr))
            # print(line)
            try:
                # if line_arr[3] == "Worker.Units.Gpio":
                # if line_arr[1] == "22:42:22": #or line_arr[1] == "22:13:41" or line_arr[1] == "22:13:43":
                if line_arr[4]=='ERROR' or line_arr[4]=='CRITICAL':
                    if line_arr[3] == 'Worker.Units.TempSensor.DHTWrapper':
                        pass
                    else:
                        print(line[:-1])
                        the_file.write(line[:])
                # if line_arr[3] == "Worker.Units.Gpio":# and line_arr[5] == 'update_state coro started':
                    # if line_arr[5] == 'Airflow and calibration started\n':
                    # print(line[:-1])
            except Exception as e:
                # print(line)
                # print(line_arr[3])
                pass
        pass
    f.close()


if __name__ == "__main__":
    parse("../data/data_1340/worker_1340.log")