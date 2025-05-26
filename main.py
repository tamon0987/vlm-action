import time
import tagurobo

# SDKの使用例
def main():
    # SDKのインスタンスを作成（IPアドレスとポートを指定）
    # arm = tagurobo.RobotArmSDK(ip_address="192.168.11.10", port=4210, num_joints=6)
    arm = tagurobo.RobotArmSDK(ip_address="0.0.0.0", port=4210, num_joints=6)

    # ロボットアームに接続
    if not arm.connect():
        print("接続に失敗しました。終了します。")
        return
    
    try:
        # 関節の制限を設定
        arm.set_joint_limits(0, 0.0, 180.0)
        arm.set_joint_limits(1, 0.0, 180.0)
        
        # 現在の関節角度を取得して表示
        print("現在の関節角度:", arm.get_all_joint_angles())
        
        # 10回エクササイズ
        for i in range(10):
                arm.set_joint_angle(0, 0)
                time.sleep(1)
                arm.set_joint_angle(0, 90)
                time.sleep(1)
        
        print("現在の関節角度:", arm.get_all_joint_angles())

        # 少し待機
        time.sleep(2)

        # すべての関節角度を同時に設定
        arm.set_all_joint_angles([30.0, 45.0, 0.0, 0.0, 0.0, 0.0])
        
        # 軌道を実行
        trajectory = [
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],    # ホームポジション
            [30.0, 45.0, 0.0, 0.0, 0.0, 0.0],  # 位置1
            [45.0, 30.0, 15.0, 0.0, 0.0, 0.0], # 位置2
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]     # ホームに戻る
        ]
        arm.execute_trajectory(trajectory)


    finally:
        # 必ず接続を切断
        arm.disconnect()

if __name__ == "__main__":
    main()