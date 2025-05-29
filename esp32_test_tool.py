import socket
import time
import requests
import json
import argparse
from typing import List, Dict, Optional, Union

class ESP32RobotTester:
    """ESP32ロボットアームのテストツール（UDP/HTTP両対応・複数IP対応）"""

    def __init__(self, ip_addresses: Union[str, List[str]] = "127.0.0.1", udp_port: int = 4210,
                 http_port: int = 80, use_mock: bool = True):
        # 複数IP対応
        if isinstance(ip_addresses, str):
            self.ip_addresses = [ip.strip() for ip in ip_addresses.split(",")]
        else:
            self.ip_addresses = ip_addresses
        self.udp_port = udp_port
        self.http_port = http_port
        self.use_mock = use_mock
        self.base_urls = [f"http://{ip}:{http_port}" for ip in self.ip_addresses]

        # UDP用ソケット
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.settimeout(2.0)
        
    def send_udp_command(self, command: str) -> Optional[List[str]]:
        """UDPコマンドを全IPに送信して応答を取得"""
        responses = []
        for ip in self.ip_addresses:
            try:
                # コマンドに改行を追加（ESP32の実装に合わせる）
                cmd = command if command.endswith('\n') else command + '\n'
                print(f"[UDP] 送信({ip}): {cmd.strip()}")
                self.udp_sock.sendto(cmd.encode('utf-8'), (ip, self.udp_port))
                # 応答を待機
                data, addr = self.udp_sock.recvfrom(1024)
                response = data.decode('utf-8').strip()
                print(f"[UDP] 受信({ip}): {response}")
                responses.append(response)
            except socket.timeout:
                print(f"[UDP] タイムアウト({ip})")
                responses.append(None)
            except Exception as e:
                print(f"[UDP] エラー({ip}): {e}")
                responses.append(None)
        return responses if responses else None
    
    def get_http_servos(self) -> Optional[List[Dict]]:
        """HTTPで全IPのサーボ状態を取得"""
        all_servos = []
        for base_url in self.base_urls:
            try:
                response = requests.get(f"{base_url}/servos", timeout=5)
                if response.status_code == 200:
                    servos = response.json()
                    print(f"[HTTP] サーボ状態({base_url}): {servos}")
                    all_servos.append(servos)
                else:
                    print(f"[HTTP] エラー({base_url}): {response.status_code}")
                    all_servos.append(None)
            except Exception as e:
                print(f"[HTTP] エラー({base_url}): {e}")
                all_servos.append(None)
        return all_servos if all_servos else None
    
    def set_http_servos(self, servo_data: List[Dict]) -> bool:
        """HTTPで全IPのサーボを制御"""
        success = True
        for base_url in self.base_urls:
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(f"{base_url}/servos",
                                        json=servo_data,
                                        headers=headers,
                                        timeout=5)
                if response.status_code == 200:
                    result = response.json()
                    ok = result.get('status') == 'ok'
                    print(f"[HTTP] サーボ制御({base_url}): {'成功' if ok else '失敗'}")
                    success = success and ok
                else:
                    print(f"[HTTP] エラー({base_url}): {response.status_code}")
                    success = False
            except Exception as e:
                print(f"[HTTP] エラー({base_url}): {e}")
                success = False
        return success
    
    def stop_all_http(self) -> bool:
        """HTTPで全IPの全サーボを停止"""
        success = True
        for base_url in self.base_urls:
            try:
                response = requests.post(f"{base_url}/stop_all", timeout=5)
                ok = response.status_code == 200
                print(f"[HTTP] 全サーボ停止({base_url}): {'成功' if ok else '失敗'}")
                success = success and ok
            except Exception as e:
                print(f"[HTTP] エラー({base_url}): {e}")
                success = False
        return success
    
    def angle_to_pwm(self, angle: float, max_angle: int = 180) -> int:
        """角度をPWM値に変換"""
        if angle <= 0:
            angle = 0
        if angle >= max_angle:
            angle = max_angle
        pulse_msec = angle * (2.0 / max_angle) + 0.5
        pulse_step = int(pulse_msec / 0.0048828125)
        return pulse_step
    
    def pwm_to_angle(self, pwm_value: int, max_angle: int = 180) -> float:
        """PWM値を角度に変換"""
        pulse_msec = 0.0048828125 * pwm_value
        angle = ((pulse_msec - 0.5) / 2.0) * max_angle
        if angle <= 0.0:
            angle = 0
        if angle >= max_angle:
            angle = max_angle
        return angle
    
    def test_udp_connection(self):
        """UDP接続テスト"""
        print("\n=== UDP接続テスト ===")
        response = self.send_udp_command("CONNECT")
        if response == "OK":
            print("✓ 接続成功")
            return True
        else:
            print("✗ 接続失敗")
            return False
    
    def test_udp_joint_control(self):
        """UDP関節制御テスト"""
        print("\n=== UDP関節制御テスト ===")
        
        # 単一関節
        print("\n1. 単一関節制御")
        response = self.send_udp_command("SET_JOINT_ANGLE,0,45.0,30.0")
        print(f"   結果: {response}")
        time.sleep(2)
        
        # 角度取得
        response = self.send_udp_command("GET_JOINT_ANGLES")
        if response:
            angles = response.split(',')
            print(f"   現在角度: {angles}")
        
        # 全関節
        print("\n2. 全関節制御")
        response = self.send_udp_command("SET_ALL_JOINT_ANGLES,10,-10,20,-20,30,-30,40.0")
        print(f"   結果: {response}")
        time.sleep(2)
        
        # 角度取得
        response = self.send_udp_command("GET_JOINT_ANGLES")
        if response:
            angles = response.split(',')
            print(f"   現在角度: {angles}")
        
        # ホームポジション
        print("\n3. ホームポジション復帰")
        response = self.send_udp_command("SET_ALL_JOINT_ANGLES,0,0,0,0,0,0,50.0")
        print(f"   結果: {response}")
    
    def test_http_control(self):
        """HTTP制御テスト"""
        print("\n=== HTTP制御テスト ===")
        
        # 現在状態取得
        print("\n1. サーボ状態取得")
        servos = self.get_http_servos()
        if servos:
            for servo in servos[:6]:  # 最初の6個のみ表示
                angle = self.pwm_to_angle(servo['off_time'])
                print(f"   サーボ{servo['id']}: PWM={servo['off_time']}, 角度={angle:.1f}°")
        
        # サーボ制御
        print("\n2. HTTP経由でサーボ制御")
        servo_commands = []
        for i in range(6):
            angle = 30.0 if i % 2 == 0 else -30.0
            pwm = self.angle_to_pwm(angle)
            servo_commands.append({
                'id': i,
                'on_time': 0,
                'off_time': pwm
            })
        
        if self.set_http_servos(servo_commands):
            print("   ✓ サーボ制御成功")
        else:
            print("   ✗ サーボ制御失敗")
        
        time.sleep(2)
        
        # 停止
        print("\n3. 全サーボ停止")
        if self.stop_all_http():
            print("   ✓ 停止成功")
        else:
            print("   ✗ 停止失敗")
    
    def test_combined_control(self):
        """UDP/HTTP組み合わせテスト"""
        print("\n=== UDP/HTTP組み合わせテスト ===")
        
        # UDPで制御
        print("\n1. UDPで関節を30度に設定")
        self.send_udp_command("SET_ALL_JOINT_ANGLES,30,30,30,30,30,30,50.0")
        time.sleep(2)
        
        # HTTPで確認
        print("\n2. HTTPで状態確認")
        servos = self.get_http_servos()
        if servos:
            for servo in servos[:6]:
                angle = self.pwm_to_angle(servo['off_time'])
                print(f"   サーボ{servo['id']}: 角度={angle:.1f}°")
        
        # HTTPで制御
        print("\n3. HTTPで0度に戻す")
        servo_commands = []
        for i in range(6):
            servo_commands.append({
                'id': i,
                'on_time': 0,
                'off_time': self.angle_to_pwm(0)
            })
        self.set_http_servos(servo_commands)
        time.sleep(2)
        
        # UDPで確認
        print("\n4. UDPで状態確認")
        response = self.send_udp_command("GET_JOINT_ANGLES")
        if response:
            angles = response.split(',')
            for i, angle in enumerate(angles[:6]):
                print(f"   関節{i}: {float(angle):.1f}°")
    
    def interactive_mode(self):
        """対話モード"""
        print("\n=== 対話モード ===")
        print("コマンド例:")
        print("  CONNECT")
        print("  GET_JOINT_ANGLES")
        print("  SET_JOINT_ANGLE,0,45.0,30.0")
        print("  SET_ALL_JOINT_ANGLES,10,-10,20,-20,30,-30,40.0")
        print("  DISCONNECT")
        print("  quit - 終了")
        print("")
        
        while True:
            try:
                command = input("コマンド> ").strip()
                if command.lower() == 'quit':
                    break
                    
                if command:
                    self.send_udp_command(command)
                    
            except KeyboardInterrupt:
                print("\n終了します")
                break
    
    def run_all_tests(self):
        """全テストを実行"""
        print("ESP32ロボットアーム統合テスト開始")
        print(f"対象: {self.ip_address}")
        print(f"UDP: {self.udp_port}, HTTP: {self.http_port}")
        print("="*50)
        
        # UDP接続テスト
        if not self.test_udp_connection():
            print("\nUDP接続に失敗しました。")
            return
        
        # 各種テスト
        self.test_udp_joint_control()
        
        if not self.use_mock:  # 実機の場合のみHTTPテスト
            self.test_http_control()
            self.test_combined_control()
        
        # 切断
        print("\n=== 切断 ===")
        self.send_udp_command("DISCONNECT")
        print("✓ テスト完了")


def main():
    parser = argparse.ArgumentParser(description='ESP32ロボットアームテストツール')
    parser.add_argument('--ip', default='127.0.0.1', help='IPアドレス（カンマ区切りで複数指定可）')
    parser.add_argument('--udp-port', type=int, default=4210, help='UDPポート')
    parser.add_argument('--http-port', type=int, default=80, help='HTTPポート')
    parser.add_argument('--mock', action='store_true', help='モックサーバーを使用')
    parser.add_argument('--interactive', '-i', action='store_true', help='対話モード')
    
    args = parser.parse_args()
    
    # 複数IP対応
    ip_list = [ip.strip() for ip in args.ip.split(",")]
    if not args.mock and all(ip == '127.0.0.1' for ip in ip_list):
        print("実機を使用する場合は --ip オプションでIPアドレスを指定してください")
        print("例: python esp32_test_tool.py --ip 192.168.11.10")
        return

    tester = ESP32RobotTester(
        ip_addresses=ip_list,
        udp_port=args.udp_port,
        http_port=args.http_port,
        use_mock=args.mock
    )
    
    if args.interactive:
        tester.interactive_mode()
    else:
        tester.run_all_tests()


if __name__ == "__main__":
    main()