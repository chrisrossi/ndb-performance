import requests
import sys

N = 1000
ROUND = 3  # milliseconds


def main():
    base_url = sys.argv[1]

    def get(path):
        url = base_url + path
        return requests.get(url).text.strip()

    def get_times(path):
        """Parse output of test to get times.

        Example output:

            211
            time: 0.8116917610168457
            rpc_time: 0.7433881759643555 (91%)
            wait_time: 0.742734432220459 (91%)
        """
        times = {}
        for line in get(path).split("\n"):
            if ": " not in line:
                continue

            key, value = line.split(": ")
            value = value.split(None)[0]  # Elide percentage
            times[key] = float(value)

        return times

    def runtests(path):
        # Throw away times from first run, but use it to initialize structure
        sums = {key: 0 for key in get_times(path).keys()}

        test_runs = (get_times(path) for _ in range(N))
        for times in test_runs:
            for key, value in times.items():
                sums[key] += value

        rounded_averages = {
            key: round(value / N, ROUND)
            for key, value in sums.items()
        }
        return rounded_averages

    def format_times(times):
        total = times.pop("time")
        lines = ["time: {}".format(total)]
        for key, value in sorted(times.items()):
            percent = int(round(value * 100 / total, 0))
            lines.append(f"{key}: {value} ({percent}%)")

        return "\n".join(lines)

    print(f"Checking {base_url}")
    assert get("/") == "ok"
    print("ok")

    print("Clean up")
    print(get("/cleanup"))

    print("Initialize")
    print(get("/init"))

    print("Test 1")
    print(format_times(runtests("/test1")))

    print("Test 2")
    print(format_times(runtests("/test2")))

    print("Clean up")
    print(get("/cleanup"))


if __name__ == "__main__":
    main()
