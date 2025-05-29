import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D # 3Dプロットに必須
import numpy as np
import matplotlib.animation as animation
import socket
import time

# --- サーバー設定 ---
SERVER_HOST = '127.0.0.1'  # モックサーバーのホスト
SERVER_PORT = 4210         # モックサーバーのポート
UDP_TIMEOUT = 0.5          # UDP受信のタイムアウト (秒)

# --- ロボットアーム設定 ---
# モックサーバーのデフォルト関節数は6
NUM_JOINTS = 6
# 各リンクの長さ (実際のロボットアームに合わせて調整してください)
LINK_LENGTHS = [35, 160, 120, 90, 65, 36] # 例: 6関節アーム
if len(LINK_LENGTHS) != NUM_JOINTS:
    raise ValueError(f"LINK_LENGTHSの要素数({len(LINK_LENGTHS)})がNUM_JOINTS({NUM_JOINTS})と一致しません。")

ANIMATION_INTERVAL = 50 # アニメーションのフレーム間隔 (ミリ秒) - サーバーへの問い合わせ頻度

# --- UDPソケットの準備 ---
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_socket.settimeout(UDP_TIMEOUT)

# サーバーに接続メッセージを送信 (オプション)
try:
    print(f"サーバー {SERVER_HOST}:{SERVER_PORT} に接続試行中...")
    udp_socket.sendto("CONNECT".encode('utf-8'), (SERVER_HOST, SERVER_PORT))
    response, _ = udp_socket.recvfrom(1024)
    print(f"サーバー接続応答: {response.decode('utf-8')}")
except socket.timeout:
    print("警告: サーバーへのCONNECT要求がタイムアウトしました。")
    print("続行しますが、サーバーが起動していないか、応答がない可能性があります。")
except ConnectionRefusedError:
    print(f"エラー: サーバー {SERVER_HOST}:{SERVER_PORT} に接続できませんでした。")
    print("モックサーバーが起動しているか確認してください。スクリプトを終了します。")
    exit()
except Exception as e:
    print(f"サーバー接続中に予期せぬエラー: {e}")
    exit()


def get_angles_from_server():
    """モックサーバーから現在の関節角度を取得する"""
    try:
        udp_socket.sendto("GET_JOINT_ANGLES".encode('utf-8'), (SERVER_HOST, SERVER_PORT))
        data, _ = udp_socket.recvfrom(1024) # buffer size 1024
        angles_deg_str = data.decode('utf-8').split(',')
        
        if len(angles_deg_str) == NUM_JOINTS:
            # サーバーから来る角度は度数法なのでラジアンに変換
            angles_rad = [np.deg2rad(float(a)) for a in angles_deg_str]
            return angles_rad
        else:
            print(f"エラー: サーバーから予期しない数の関節角度が返されました。受信: {len(angles_deg_str)}, 期待: {NUM_JOINTS}")
            return None
    except socket.timeout:
        # print("警告: GET_JOINT_ANGLES サーバーからの応答がタイムアウトしました。") # 頻繁に出る場合はコメントアウト
        return None
    except ValueError as e:
        print(f"エラー: サーバーからの角度データの変換に失敗: {e}. データ: '{data.decode('utf-8')}'")
        return None
    except Exception as e:
        print(f"エラー: サーバーからの角度取得中にエラー: {e}")
        return None

def forward_kinematics(angles_rad, link_lengths):
    """
    ロボットアームの順運動学を計算します。
    初期状態(全関節角度0度)でZ-axis方向に伸び、各関節の角度はY-axis周りの回転(ピッチ)として作用します。
    """
    num_links = len(link_lengths)
    joint_positions = np.zeros((num_links + 1, 3)) # ベース + 各関節先端の座標

    current_position = np.array([0.0, 0.0, 0.0])  # ベースの位置 (原点)
    joint_positions[0, :] = current_position

    # Y-axis周りの累積回転角 (ピッチ角)
    # 各 angles_rad[i] は、前のリンクの方向からの相対的なピッチ角と解釈し、
    # それをワールド座標系でのY-axis周りの回転として単純化して適用します。
    # (より正確な多関節モデルでは、各リンクのローカル座標系を追跡する必要があります)
    cumulative_pitch_angle = 0.0

    for i in range(num_links):
        # この関節でのピッチ角を累積 (アーム全体が同じXZ平面で曲がる簡易モデル)
        cumulative_pitch_angle += angles_rad[i]
        
        # XZ平面内での回転を計算
        # 角度0 (cumulative_pitch_angle が 0) のとき、
        # sin(0)=0, cos(0)=1 となり、Z-axis方向にのみ伸びます (dx=0, dz=link_length)。
        
        # 現在のリンクの長さの各-axisへの射影を計算
        # dx: X-axis方向の変位
        # dy: Y-axis方向の変位 (Y-axis周りの回転なので0)
        # dz: Z-axis方向の変位
        dx = link_lengths[i] * np.sin(cumulative_pitch_angle)
        dy = 0.0 # Y-axis周りの回転なので、Y方向への直接的な伸びはない
        dz = link_lengths[i] * np.cos(cumulative_pitch_angle)
        
        # 新しい関節位置を計算
        # current_position は前の関節の先端位置（このループの開始時点での値）
        current_position = current_position + np.array([dx, dy, dz])
        joint_positions[i+1, :] = current_position
        
    return joint_positions

# --- 3Dプロットの準備 ---
fig = plt.figure(figsize=(9, 9))
ax = fig.add_subplot(111, projection='3d')

# 描画範囲の初期設定 (アームの最大リーチに基づいて大まかに設定)
max_reach = sum(LINK_LENGTHS)
ax.set_xlim([-max_reach * 1.1, max_reach * 1.1])
ax.set_ylim([-max_reach * 1.1, max_reach * 1.1])
ax.set_zlim([-max_reach * 0, max_reach * 1.1]) # Z-axisの範囲は適宜調整

ax.set_xlabel('X-axis')
ax.set_ylabel('Y-axis')
ax.set_zlabel('Z-axis')
ax.set_title('robot arm 3D visualization (server simulation)')
ax.view_init(elev=25., azim=45)

line, = ax.plot([], [], [], 'o-', lw=3, markersize=7, color='deepskyblue', markeredgecolor='navy')
base_point, = ax.plot([], [], [], 'o', markersize=12, color='crimson')

# 現在のロボットの角度を保持 (ラジアン) - 初期値はゼロ
current_robot_angles_rad = [0.0] * NUM_JOINTS
last_successful_angles_rad = list(current_robot_angles_rad) # 最後に成功した角度を保持

def init_animation():
    line.set_data_3d([], [], [])
    base_point.set_data_3d([], [], [])
    return line, base_point,

def update_animation(frame_index):
    global last_successful_angles_rad # 最後に成功した角度を更新可能にする
    
    # サーバーから現在の関節角度を取得
    new_angles_rad = get_angles_from_server()
    
    angles_to_use_rad = last_successful_angles_rad # デフォルトは最後に成功した角度
    if new_angles_rad:
        angles_to_use_rad = new_angles_rad
        last_successful_angles_rad = new_angles_rad # 成功したら更新
    
    joint_positions = forward_kinematics(angles_to_use_rad, LINK_LENGTHS)
    
    x_coords = joint_positions[:, 0]
    y_coords = joint_positions[:, 1]
    z_coords = joint_positions[:, 2]
    
    line.set_data_3d(x_coords, y_coords, z_coords)
    base_point.set_data_3d([0], [0], [0])
    
    angles_deg_str = ", ".join([f"{np.rad2deg(a):.1f}" for a in angles_to_use_rad])
    ax.set_title(f'関節角度 (度): {angles_deg_str}')
    
    return line, base_point,

# アニメーションオブジェクトの作成
ani = animation.FuncAnimation(fig, update_animation, frames=None, # リアルタイム更新のためNone
                              init_func=init_animation, blit=True,
                              interval=ANIMATION_INTERVAL, repeat=False)

# ウィンドウクローズ時の処理
def on_close(event):
    print("ウィンドウが閉じられました。サーバーから切断します...")
    try:
        udp_socket.sendto("DISCONNECT".encode('utf-8'), (SERVER_HOST, SERVER_PORT))
        # 応答は待たなくても良い場合もある
        # response, _ = udp_socket.recvfrom(1024)
        # print(f"サーバー切断応答: {response.decode('utf-8')}")
    except Exception as e:
        print(f"サーバーからの切断中にエラー: {e}")
    finally:
        udp_socket.close()
        print("ソケットをクローズしました。")

fig.canvas.mpl_connect('close_event', on_close)

plt.tight_layout()
plt.show()

print("3D可視化スクリプト終了。")