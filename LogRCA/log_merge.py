import re
import heapq

# 需要合并的日志文件列表（请替换为你的文件名）
log_files = ["OpenStack/openstack_abnormal.log", "OpenStack/openstack_normal1.log", "OpenStack/openstack_normal2.log"]  
output_file = "OpenStack/merged_logs.log"  

# 日志时间戳正则匹配
TIMESTAMP_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)")

def extract_timestamp(log_line):
    """ 从日志行中提取时间戳 """
    match = TIMESTAMP_PATTERN.search(log_line)
    return match.group(0) if match else None

def merge_logs(log_files, output_file):
    """ 按时间戳排序合并多个日志文件 """
    log_entries = []

    # 读取所有日志文件
    for log_file in log_files:
        with open(log_file, "r") as f:
            for line in f:
                timestamp = extract_timestamp(line)
                if timestamp:
                    log_entries.append((timestamp, line))  # 记录 (时间戳, 日志内容)

    # 按时间戳排序
    log_entries.sort(key=lambda x: x[0])  

    # 写入合并后的日志文件
    with open(output_file, "w") as f:
        for _, line in log_entries:
            f.write(line)

if __name__ == "__main__":
    merge_logs(log_files, output_file)
    print(f"合并完成，输出文件：{output_file}")
