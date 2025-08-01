import cv2, numpy as np, pathlib, subprocess, argparse, os, glob

def validate_target(target):
    """TARGET値が36の倍数+1であることを確認"""
    if (target - 1) % 36 != 0:
        raise ValueError(f"TARGET値は36の倍数+1である必要があります。指定値: {target}")
    return target

def get_video_files(src_path):
    """SRCパスから動画ファイルを取得"""
    if os.path.isfile(src_path):
        return [src_path]
    elif os.path.isdir(src_path):
        video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv', '*.webm']
        video_files = []
        for ext in video_extensions:
            video_files.extend(glob.glob(os.path.join(src_path, ext)))
        if not video_files:
            raise ValueError(f"指定ディレクトリに動画ファイルが見つかりません: {src_path}")
        return video_files
    else:
        raise ValueError(f"指定されたパスが存在しません: {src_path}")

def process_video(src_file, target):
    """動画を処理してフレームを抽出"""
    cap = cv2.VideoCapture(src_file)
    frames, scores = [], []
    _, prev = cap.read()
    if prev is None:
        raise ValueError(f"動画ファイルを読み込めません: {src_file}")

    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret: break
        diff = cv2.absdiff(frame,prev)
        scores.append((np.mean(diff), idx))
        frames.append(frame); prev = frame; idx+=1
    cap.release()

    if len(frames) < target:
        print(f"警告: 動画のフレーム数({len(frames)})がTARGET値({target})より少ないため、全フレームを使用します。")
        target = len(frames)

    # スコアが大きい順に間引き（動きの大きいフレームを優先）
    # 厳密にtarget数のフレームを選択
    if len(scores) >= target:
        # 最初と最後のフレームは必ず保持
        first_frame = 0
        last_frame = len(frames) - 1

        if target <= 2:
            # target数が2以下の場合は最初と最後のフレームのみ
            keep_idx = [first_frame, last_frame] if target == 2 else [first_frame]
        else:
            # 最初と最後のフレームを除いた中間フレームから選択
            middle_scores = [(score, idx) for score, idx in scores if idx != first_frame and idx != last_frame]

            # 中間フレームから target-2 個選択
            middle_keep = sorted(middle_scores, key=lambda x:x[0], reverse=True)[:target-2]
            middle_keep_idx = [idx for _, idx in middle_keep]

            # 最初、中間、最後のフレームを結合
            keep_idx = [first_frame] + sorted(middle_keep_idx) + [last_frame]
    else:
        # フレーム数がターゲット数より少ない場合は全フレームを使用
        keep_idx = list(range(len(frames)))
        target = len(frames)

    print(f"選択されたフレーム数: {len(keep_idx)} / 元のフレーム数: {len(frames)}")
    print(f"保持されるフレーム: 最初={keep_idx[0]}, 最後={keep_idx[-1]}")

    return frames, keep_idx

def main():
    parser = argparse.ArgumentParser(description='動画からフレームを抽出して新しい動画を作成')
    parser.add_argument('src', help='入力動画ファイル またはディレクトリ')
    parser.add_argument('--target', type=int, default=109, help='出力フレーム数（36の倍数+1、デフォルト: 109）')
    parser.add_argument('--replace', action='store_true', help='元ファイルを上書きする（デフォルト: 新しいファイルを作成）')

    args = parser.parse_args()

    # TARGET値の検証
    validate_target(args.target)

    # 動画ファイルの取得
    video_files = get_video_files(args.src)

    for video_file in video_files:
        print(f"処理中: {video_file}")

        # 動画処理
        frames, keep_idx = process_video(video_file, args.target)

        # 実際に選択されたフレーム数を確認
        if len(keep_idx) != args.target and len(frames) >= args.target:
            print(f"エラー: 期待されるフレーム数({args.target})と実際のフレーム数({len(keep_idx)})が一致しません")
            continue

        # 出力ファイル名を生成
        base_name = os.path.splitext(os.path.basename(video_file))[0]
        if args.replace:
            # 元ファイルを上書きする場合
            output_name = video_file
            temp_output = f"{base_name}_temp.mp4"
        else:
            # 新しいファイルを作成する場合
            output_name = f"{base_name}_out.mp4"
            temp_output = output_name
        list_name = f"{base_name}_list.txt"

        # ffmpeg concat listを生成
        png_files = []
        for idx, i in enumerate(keep_idx):
            # 連番のファイル名を作成（ffmpegで使いやすくするため）
            out=f"{base_name}_f_{idx:04d}.png"
            png_files.append(out)
            success = cv2.imwrite(out, frames[i])
            if not success:
                print(f"警告: PNGファイルの書き込みに失敗しました: {out}")
                continue

        print(f"作成されたPNGファイル数: {len(png_files)}")

        # 元の動画のフレームレートを取得
        cap_info = cv2.VideoCapture(video_file)
        fps = cap_info.get(cv2.CAP_PROP_FPS)
        if fps == 0:
            fps = 30  # デフォルトのフレームレート
        cap_info.release()

        print(f"元の動画のフレームレート: {fps} fps")

        # ffmpegで動画を作成（PNGシーケンスから直接作成）
        pattern = f"{base_name}_f_%04d.png"
        cmd = f"ffmpeg -y -r {fps} -i {pattern} -c:v libx264 -pix_fmt yuv420p -preset medium -crf 23 -movflags +faststart {temp_output}"
        print(f"実行コマンド: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"ffmpegエラー: {result.stderr}")
            # エラーが発生した場合、別のアプローチを試す
            print("別のffmpegコマンドを試しています...")
            cmd2 = f"ffmpeg -y -framerate {fps} -i {pattern} -c:v libx264 -pix_fmt yuv420p -r {fps} {temp_output}"
            result2 = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
            if result2.returncode != 0:
                print(f"2回目のffmpegエラー: {result2.stderr}")
                continue
            else:
                print("2回目のffmpegコマンドが成功しました")
        else:
            print("ffmpegコマンドが成功しました")

        # replaceオプションが指定されている場合、元ファイルを置き換える
        if args.replace and temp_output != output_name:
            os.replace(temp_output, output_name)

        # 一時ファイルをクリーンアップ
        try:
            # PNGファイルも削除
            for png_file in png_files:
                if os.path.exists(png_file):
                    os.remove(png_file)
        except Exception as e:
            print(f"一時ファイルの削除に失敗: {e}")

        if args.replace:
            print(f"ファイルを上書きしました: {output_name}")
        else:
            print(f"出力完了: {output_name}")

if __name__ == "__main__":
    main()
