def get_input():
    user_input = input("请输入数据：")
    return user_input

def process_data_1(data):
    if data.isdigit():
        return int(data) * 2
    else:
        return data + "_suffix"

def process_data_2(data):
    return data[::-1]

def process_data_3(data):
    return data.upper()

def branch_1(data):
    result = process_data_1(data)
    dangerous_function_a(result)

def branch_2(data):
    result = process_data_2(data)
    dangerous_function_b(result)

def branch_3(data):
    result = process_data_3(data)
    dangerous_function_c(result)

def dangerous_function_a(data):
    eval(data)  # 危险函数调用

def dangerous_function_b(data):
    exec(data)  # 危险函数调用

def dangerous_function_c(data):
    import os
    os.system(data)  # 危险函数调用

def main():
    data = get_input()
    branch_1(data)
    branch_2(data)
    branch_3(data)

if __name__ == "__main__":
    main()
