import socket
import datetime
import sys
import threading
import time
import math
from typing import Dict, List, Optional

class ESP32RobotMockServer:
    """
    ESP32ロボットアームのモックサーバー（実際のプロトコルに準拠）
    """
    
    def __init__(self, host: str = '127.0.0.1', port: int = 4210, num_joints: int = 6):
        self.host = host
        self.port = port
        self.num_joints = num_joints
        self.sock = None
        self.running = False
        
        # ロボットの状態
        self.connected_clients = set()
        self.joint_angles = [0.0] * num_joints
        self.joint_speeds = [50.0] * num_joints
        
        # サーボのPWM状態をシミュレート
        self.servo_pwm = []
        for i in range(num_joints):
            self.servo_pwm.append({
                'on_time': 0,
                'off_time': self._angle_to_pwm(0.0)
            })
        
        # 動作シミュレーション用
        self.movement_threads = {}
        self.movement_stop_flags = {}
        
    def _angle_to_pwm(self, angle: float, max_angle: int = 180) -> int:
        """角度をPWM値に変換（ESP32の実装に合わせる）"""
        if angle <= 0:
            angle = 0
        if angle >= max_angle:
            angle = max_angle
            
        # pulse_msec = angle * (2.0 / max_angle) + 0.5
        pulse_msec = angle * (2.0 / max_angle) + 0.5
        # 50Hz -> 20msec, 20 / 4096 = 0.0048828125
        pulse_step = int(pulse_msec / 0.0048828125)
        return pulse_step
    
    def _pwm_to_angle(self, pwm_value: int, max_angle: int = 180) -> float:
        """PWM値を角度に変換"""
        pulse_msec = 0.0048828125 * pwm_value
        angle = ((pulse_msec - 0.5) / 2.0) * max_angle
        if angle <= 0.0:
            angle = 0
        if angle >= max_angle:
            angle = max_angle
        return angle
    
    def start(self):
        """サーバーを起動"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        self.running = True
        
        print(f"ESP32 ロボットアームモックサーバー起動")
        print(f"アドレス: {self.host}:{self.port}")
        print(f"関節数: {self.num_joints}")
        print("-" * 50)
        
        try:
            while self.running:
                # データを受信
                data, addr = self.sock.recvfrom(1024)
                
                # 別スレッドで処理
                thread = threading.Thread(target=self._handle_request, args=(data, addr))
                thread.daemon = True
                thread.start()
                
        except KeyboardInterrupt:
            print("\n\nサーバーを終了します...")
        finally:
            self.stop()
    
    def stop(self):
        """サーバーを停止"""
        self.running = False
        # すべての動作を停止
        for flag in self.movement_stop_flags.values():
            flag.set()
        if self.sock:
            self.sock.close()
    
    def _handle_request(self, data: bytes, addr: tuple):
        """リクエストを処理"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        try:
            # データをデコード
            command = data.decode('utf-8').strip()  # 改行コードを削除
            print(f"\n[{timestamp}] 受信 from {addr[0]}:{addr[1]}")
            print(f"コマンド: [{command}]")
            
            # レスポンスを生成
            response = self._process_command(command, addr)
            
            # レスポンスを送信（改行コードなし）
            if response:
                self.sock.sendto(response.encode('utf-8'), addr)
                print(f"応答: [{response}]")
            
            print("-" * 50)
            
        except Exception as e:
            print(f"エラー: {e}")
            error_response = f"ERROR: {str(e)}"
            self.sock.sendto(error_response.encode('utf-8'), addr)
    
    def _process_command(self, command: str, addr: tuple) -> str:
        """コマンドを処理してレスポンスを返す"""
        parts = command.split(',')
        cmd = parts[0]
        
        # 接続管理
        if cmd == "CONNECT":
            self.connected_clients.add(addr)
            print(f"✓ クライアント接続: {addr}")
            return "OK"
            
        elif cmd == "DISCONNECT":
            self.connected_clients.discard(addr)
            print(f"✓ クライアント切断: {addr}")
            return "OK"
            
        # 状態取得
        elif cmd == "GET_JOINT_ANGLES":
            # 現在のPWM値から角度を計算
            angles = []
            for i in range(self.num_joints):
                angle = self._pwm_to_angle(self.servo_pwm[i]['off_time'])
                angles.append(f"{angle:.2f}")
            angles_str = ",".join(angles)
            print(f"→ 現在の関節角度: {angles_str}")
            return angles_str
            
        # 関節制御
        elif cmd == "SET_JOINT_ANGLE":
            if len(parts) >= 4:
                try:
                    joint_id = int(parts[1])
                    angle = float(parts[2])
                    speed = float(parts[3])
                    
                    if 0 <= joint_id < self.num_joints:
                        # 動作シミュレーション
                        self._simulate_joint_movement(joint_id, angle, speed)
                        print(f"✓ 関節{joint_id}を{angle}°に設定 (速度: {speed}°/s)")
                        return "OK"
                    else:
                        print(f"✗ 無効な関節ID: {joint_id}")
                        return "NG"
                except ValueError as e:
                    print(f"✗ パラメータエラー: {e}")
                    return "NG"
            print("✗ パラメータ不足")
            return "NG"
            
        elif cmd == "SET_ALL_JOINT_ANGLES":
            if len(parts) >= self.num_joints + 2:  # コマンド + 6角度 + 速度
                try:
                    angles = []
                    for i in range(self.num_joints):
                        angle = float(parts[i + 1])
                        angles.append(angle)
                    speed = float(parts[self.num_joints + 1])
                    
                    # 全関節の動作シミュレーション
                    for i, angle in enumerate(angles):
                        self._simulate_joint_movement(i, angle, speed)
                    
                    print(f"✓ 全関節角度設定: {angles} (速度: {speed}°/s)")
                    return "OK"
                    
                except ValueError as e:
                    print(f"✗ パラメータエラー: {e}")
                    return "NG"
            print(f"✗ パラメータ不足: {len(parts)} < {self.num_joints + 2}")
            return "NG"
            
        elif cmd == "EMERGENCY_STOP":
            # すべての動作を停止
            for flag in self.movement_stop_flags.values():
                flag.set()
            print("⚠️ 緊急停止実行")
            return "OK"
            
        elif cmd == "GET_SYSTEM_STATUS":
            # 拡張コマンド（オプション）
            import json
            status = {
                "status": "READY",
                "joints": self.joint_angles,
                "connected_clients": len(self.connected_clients)
            }
            return json.dumps(status)
            
        else:
            print(f"✗ 不明なコマンド: [{cmd}]")
            return f"ERROR: Unknown command: {cmd}"
    
    def _simulate_joint_movement(self, joint_id: int, target_angle: float, speed: float):
        """関節の動作をシミュレート"""
        # 既存の動作を停止
        if joint_id in self.movement_stop_flags:
            self.movement_stop_flags[joint_id].set()
            if joint_id in self.movement_threads:
                self.movement_threads[joint_id].join(timeout=0.1)
        
        # 停止フラグを作成
        stop_flag = threading.Event()
        self.movement_stop_flags[joint_id] = stop_flag
        
        def move():
            current_pwm = self.servo_pwm[joint_id]['off_time']
            start_angle = self._pwm_to_angle(current_pwm)
            target_pwm = self._angle_to_pwm(target_angle)
            
            delta = target_angle - start_angle
            
            if abs(delta) < 0.01:  # すでに目標位置
                return
                
            duration = abs(delta) / speed if speed > 0 else 0
            steps = int(duration * 20)  # 20Hz更新
            steps = max(steps, 1)
            
            print(f"  → 関節{joint_id}動作開始: {start_angle:.1f}° → {target_angle:.1f}° ({duration:.1f}秒)")
            
            start_time = time.time()
            for i in range(steps + 1):
                if stop_flag.is_set():
                    print(f"  → 関節{joint_id}動作中断")
                    break
                    
                progress = i / steps if steps > 0 else 1
                current_angle = start_angle + delta * progress
                current_pwm = self._angle_to_pwm(current_angle)
                
                self.servo_pwm[joint_id]['off_time'] = current_pwm
                self.joint_angles[joint_id] = current_angle
                
                if i % 20 == 0:  # 1秒ごとに進捗表示
                    elapsed = time.time() - start_time
                    print(f"  → 関節{joint_id}: {current_angle:.1f}° ({progress*100:.0f}%) [{elapsed:.1f}秒]")
                    
                time.sleep(0.05)  # 50ms = 20Hz
            
            if not stop_flag.is_set():
                # 最終位置を確実にセット
                self.servo_pwm[joint_id]['off_time'] = target_pwm
                self.joint_angles[joint_id] = target_angle
                print(f"  → 関節{joint_id}動作完了: {target_angle:.1f}°")
        
        # 新しい動作スレッドを開始
        thread = threading.Thread(target=move)
        thread.daemon = True
        thread.start()
        self.movement_threads[joint_id] = thread


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ESP32 ロボットアームモックサーバー')
    parser.add_argument('--host', default='127.0.0.1', help='ホストアドレス')
    parser.add_argument('--port', type=int, default=4210, help='ポート番号')
    parser.add_argument('--joints', type=int, default=6, help='関節数')
    
    args = parser.parse_args()
    
    # 簡易テストモード
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        print("=== 簡易テストモード ===")
        print("別ターミナルで以下のコマンドを実行してください:")
        print(f"echo -n 'CONNECT' | nc -u {args.host} {args.port}")
        print(f"echo -n 'GET_JOINT_ANGLES' | nc -u {args.host} {args.port}")
        print(f"echo -n 'SET_JOINT_ANGLE,0,45.0,30.0' | nc -u {args.host} {args.port}")
        print(f"echo -n 'SET_ALL_JOINT_ANGLES,10,-10,20,-20,30,-30,40.0' | nc -u {args.host} {args.port}")
        print()
    
    server = ESP32RobotMockServer(host=args.host, port=args.port, num_joints=args.joints)
    server.start()


if __name__ == "__main__":
    main()