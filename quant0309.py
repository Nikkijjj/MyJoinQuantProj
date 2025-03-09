import pandas as pd
import pandas_ta as ta
import akshare as ak
from datetime import datetime, timedelta
import matplotlib.pyplot as plt


# ========== 数据获取模块 ==========
def fetch_stock_data(symbol, start_date, end_date):
    """通过AKShare获取股票历史数据（日线）"""
    try:
        print(f"正在获取股票 {symbol} 的数据...")
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust='')
        print(f"获取到的数据:\n{df.head()}")  # 打印前几行数据
        df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume'
        }, inplace=True)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df
    except Exception as e:
        print(f"数据获取失败: {e}")
        return None


# ========== 指标计算模块（使用 pandas_ta）==========
def calculate_indicators(df):
    """计算技术指标：均线、MACD、RSI、BOLL、成交量"""
    # 均线 (5日, 20日)
    df['ma5'] = df.ta.sma(length=5)
    df['ma20'] = df.ta.sma(length=20)

    # MACD (默认参数：fast=12, slow=26, signal=9)
    macd = df.ta.macd(fast=12, slow=26, signal=9)
    df = pd.concat([df, macd], axis=1)

    # RSI (14日)
    df['rsi'] = df.ta.rsi(length=14)

    # BOLL (20日)
    boll = df.ta.bbands(length=20)
    df = pd.concat([df, boll], axis=1)

    # 成交量变化率（3日平均）
    df['volume_ma3'] = df['volume'].rolling(window=3).mean()
    df['volume_pct_change'] = (df['volume'] / df['volume_ma3'].shift(1)) - 1

    # 清理列名
    df.rename(columns={
        'MACD_12_26_9': 'macd',
        'MACDs_12_26_9': 'macd_signal',
        'MACDh_12_26_9': 'macd_hist',
        'BBL_20_2.0': 'boll_lower',
        'BBM_20_2.0': 'boll_mid',
        'BBU_20_2.0': 'boll_upper'
    }, inplace=True)

    return df


# ========== 信号生成模块 ==========
def generate_signals(df):
    """根据策略生成买卖信号"""
    signals = pd.DataFrame(index=df.index)
    signals['signal'] = 0  # 0: 无信号, 1: 买入, -1: 卖出

    # 买入条件（至少满足2个）
    buy_condition = (
            (df['ma5'] > df['ma20']) &  # 均线金叉
            (df['macd'] > df['macd_signal']) &  # MACD金叉
            (df['rsi'] < 30) &  # RSI超卖
            (df['close'] < df['boll_lower']) &  # 股价触及BOLL下轨
            (df['volume_pct_change'] > 0.2)  # 成交量放大20%
    )

    # 卖出条件（任一条件触发）
    sell_condition = (
            (df['macd'] < df['macd_signal']) |  # MACD死叉
            (df['rsi'] > 70) |  # RSI超买
            (df['close'] > df['boll_upper'])  # BOLL触及上轨
    )

    signals.loc[buy_condition, 'signal'] = 1
    signals.loc[sell_condition, 'signal'] = -1
    return signals


# ========== 回测模块 ==========
def backtest_strategy(df, signals):
    # 合并信号列到主数据框
    df = df.join(signals)
    """模拟交易回测"""
    df['position'] = signals['signal'].shift(1)  # 次日开盘执行
    df['returns'] = df['close'].pct_change()
    df['strategy_returns'] = df['position'] * df['returns']
    df['cum_returns'] = (1 + df['strategy_returns']).cumprod()
    return df

# ========== 可视化模块 ==========
def visualize_results(df, stock_name, symbol):
    """可视化价格走势、技术指标和累计收益"""
    if 'signal' not in df.columns:
        raise ValueError("缺失'signal'列，请检查信号合并流程")

    plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows 系统常用黑体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示异常

    # 创建画布和子图
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(4, 1)
    ax1 = fig.add_subplot(gs[:3, :])  # 价格和指标
    ax2 = fig.add_subplot(gs[3, :])  # 累计收益

    # 价格和指标图
    ax1.plot(df['close'], label='收盘价', linewidth=1)
    ax1.plot(df['ma5'], label='5日均线', linestyle='--', linewidth=0.8)
    ax1.plot(df['ma20'], label='20日均线', linestyle='--', linewidth=0.8)
    ax1.plot(df['boll_upper'], label='布林上轨', color='orange', linewidth=0.8)
    ax1.plot(df['boll_lower'], label='布林下轨', color='green', linewidth=0.8)

    print("signals", signals['signal'])

    # 标记买卖信号
    buy_points = df[signals['signal'] == 1]
    sell_points = df[signals['signal'] == -1]
    ax1.scatter(buy_points.index, buy_points['close'],
                marker='^', color='red', s=100, label='买入信号', zorder=5)
    ax1.scatter(sell_points.index, sell_points['close'],
                marker='v', color='green', s=100, label='卖出信号', zorder=5)

    ax1.set_title(f'{stock_name}({symbol}) 价格走势与技术指标')
    ax1.legend(loc='upper left')
    ax1.grid(True)

    # 累计收益图
    ax2.plot(df['cum_returns'], label='策略累计收益', color='purple')
    ax2.axhline(1, color='gray', linestyle='--', linewidth=0.8)  # 基准线
    ax2.set_title('累计收益率')
    ax2.set_ylabel('收益率倍数')
    ax2.legend(loc='upper left')
    ax2.grid(True)

    # 调整布局
    plt.tight_layout()

    plt.legend()
    plt.grid(True)
    plt.show()



# ========== 主程序 ==========
if __name__ == "__main__":
    # 参数设置，支持多只股票
    symbols = ["000001", "600900", "600309", "601318", "601012", "000538", "601995", "601398", "601088"]  # 可以添加更多股票代码
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

    # 获取 A 股代码和名称映射
    stock_code_name_df = ak.stock_info_a_code_name()
    print("stock_code_name_df 的列名:", stock_code_name_df.columns)  # 打印列名进行调试

    try:
        code_name_dict = dict(zip(stock_code_name_df['code'], stock_code_name_df['name']))
    except KeyError as e:
        print(f"错误: 找不到列 {e}，请检查数据格式。")
        # 可以在这里添加处理逻辑，例如使用默认的空字典
        code_name_dict = {}

    for symbol in symbols:
        # 根据代码获取股票名称
        stock_name = code_name_dict.get(symbol, "")
        if not stock_name:
            print(f"无法获取 {symbol} 的股票名称，将使用空名称继续处理。")

        # 获取数据
        df = fetch_stock_data(symbol, start_date, end_date)

        if df is None:
            continue

        # 计算指标并生成信号
        df = calculate_indicators(df)
        signals = generate_signals(df)

        # 回测并输出结果
        df = backtest_strategy(df, signals)
        visualize_results(df, stock_name, symbol)  # 使用合并后的df


        print("==========")
        print(f"===== {stock_name}({symbol}) 最新信号 =====")
        latest_date = df.index[-1].strftime('%Y-%m-%d')
        latest_signal = signals.iloc[-1]['signal']
        signal_text = '买入' if latest_signal == 1 else '卖出' if latest_signal == -1 else '无'
        latest_price = df['close'].iloc[-1]
        print(f"日期: {latest_date}, 信号: {signal_text}, 最新股价: {latest_price:.2f}")

        # 输出判定依据
        print("===== 判定依据 =====")
        latest_row = df.iloc[-1]
        if latest_signal == 1:
            conditions = [
                latest_row['ma5'] > latest_row['ma20'],
                latest_row['macd'] > latest_row['macd_signal'],
                latest_row['rsi'] < 30,
                latest_row['close'] < latest_row['boll_lower'],
                latest_row['volume_pct_change'] > 0.2
            ]
            condition_names = [
                "均线金叉",
                "MACD金叉",
                "RSI超卖",
                "股价触及BOLL下轨",
                "成交量放大20%"
            ]
            satisfied_conditions = [name for cond, name in zip(conditions, condition_names) if cond]
            print(f"买入依据: {', '.join(satisfied_conditions)}")
        elif latest_signal == -1:
            conditions = [
                latest_row['macd'] < latest_row['macd_signal'],
                latest_row['rsi'] > 70,
                latest_row['close'] > latest_row['boll_upper']
            ]
            condition_names = [
                "MACD死叉",
                "RSI超买",
                "BOLL触及上轨"
            ]
            satisfied_conditions = [name for cond, name in zip(conditions, condition_names) if cond]
            print(f"卖出依据: {', '.join(satisfied_conditions)}")
        else:
            print("无信号，不满足买卖条件。")

        # 输出股票基本信息
        print("===== 股票基本信息 =====")
        print(f"股票名称: {stock_name}")
        print(f"股票代码: {symbol}")
        print(f"数据起始日期: {start_date}")
        print(f"数据结束日期: {end_date}")

        print("===== 累计收益率 =====")
        print(f"{df['cum_returns'].iloc[-1]:.2%}")

        if not df.empty:
            visualize_results(df, stock_name, symbol)
            print(f"已生成可视化图表：{stock_name}_{symbol}_analysis.png")
        else:
            print("无有效数据可供可视化")
