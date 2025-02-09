from jqdatasdk import auth, get_price
import matplotlib.pyplot as plt

# 登录JQData
auth('account', 'password') # 账号密码自行注册

# 设置字体和负号显示
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体字体
plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

# 设置回测时间范围
start_date = '2023-10-31'
end_date = '2024-11-06'

# 获取平安银行的历史数据
data_pingan = get_price('000001.XSHE', start_date, end_date)

# 获取上证指数的历史数据
data_shanghai = get_price('000001.XSHG', start_date, end_date)

# 计算5日均线和20日均线
data_pingan['MA5'] = data_pingan['close'].rolling(window=5).mean()
data_pingan['MA20'] = data_pingan['close'].rolling(window=20).mean()

# 生成交易信号
data_pingan['Signal'] = 0
data_pingan.loc[data_pingan['MA5'] > data_pingan['MA20'], 'Signal'] = 1  # 金叉
data_pingan.loc[data_pingan['MA5'] < data_pingan['MA20'], 'Signal'] = -1  # 死叉

# 绘制策略图
plt.figure(figsize=(14, 7))
plt.plot(data_pingan.index, data_pingan['close'], label='收盘价', color='gray', alpha=0.5)
plt.plot(data_pingan.index, data_pingan['MA5'], label='MA5', color='orange')
plt.plot(data_pingan.index, data_pingan['MA20'], label='MA20', color='blue')
plt.title('平安银行双均线策略图（含交易信号标识）')
plt.xlabel('日期')
plt.ylabel('价格')

# 标记买入和卖出信号
plt.scatter(data_pingan[data_pingan['Signal'] == 1].index, data_pingan[data_pingan['Signal'] == 1]['MA5'], label='买入', marker='^', color='green')
plt.scatter(data_pingan[data_pingan['Signal'] == -1].index, data_pingan[data_pingan['Signal'] == -1]['MA20'], label='卖出', marker='v', color='red')

plt.legend()
plt.grid(True)
plt.show()