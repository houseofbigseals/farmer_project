

def parse(path):
    f = open(path)
    print(type(f))
    lines = f.readlines()
    print(len(lines))
    larr = lines[3].split(';')
    print(larr[4])
    print(larr)
    for line in lines:
        line_arr = line.split(';')
        # print(len(line_arr))
        # print(line)
        try:
            if line_arr[4]=='ERROR' or line_arr[4]=='CRITICAL':
                print(line[:-1])
            if line_arr[3] == "Worker.Units.Gpio.GpioWrapper":# and line_arr[5] == 'update_state coro started':
                # if line_arr[5] == 'Airflow and calibration started\n':
                print(line[:-1])
        except Exception as e:
            # print(line)
            # print(line_arr[3])
            pass
    pass


if __name__ == "__main__":
    parse("../data/data_1320/worker_1320.log")