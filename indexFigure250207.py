from jqdatasdk import get_price, auth
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

auth('account', 'password') # 账号密码自行注册

# 设置指数代码和时间范围
index_code = '000001.XSHG'  # 上证指数代码
start_date = '2023-10-31'
end_date = '2024-11-06'

# 获取指数数据
index_data = get_price(index_code, start_date=start_date, end_date=end_date, frequency='daily', fields='close')

# 将数据转换为DataFrame
df = pd.DataFrame(index_data)

print(df)

# 绘制指数图
plt.figure(figsize=(12, 6))
plt.plot(df.index, df['close'], label='上证指数', color='blue', linewidth=1.5)
plt.title('上证指数走势', fontsize=16)
plt.xlabel('日期', fontsize=14)
plt.ylabel('收盘价', fontsize=14)
plt.legend(fontsize=12)
plt.grid(True, linestyle='--', linewidth=0.5)
plt.show()
