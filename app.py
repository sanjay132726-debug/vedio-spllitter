import streamlit as st
import subprocess
import imageio_ffmpeg
import os
import zipfile
import tempfile
import re

st.set_page_config(page_title="Auto Video Splitter Pro", page_icon="✂️", layout="centered")

st.title("✂️ Auto Reels / Shorts Splitter (2-Hour Fast Mode)")
st.write("2 Hours video kooda seconds-la 1.5s continuity overlap-oda split pannalam!")

# 1. Video Upload (Up to 5GB)
uploaded_file = st.file_uploader("Video Upload Pannu (MP4, MKV, MOV)", type=["mp4", "mkv", "mov"])

col_opt1, col_opt2 = st.columns(2)
with col_opt1:
    clip_duration = st.selectbox(
        "Ovvoru part-um evlo seconds irukkanum?",
        options=[30, 40, 60],
        format_func=lambda x: f"{x} Seconds"
    )

with col_opt2:
    overlap_sec = st.number_input(
        "Overlap Seconds (Munnaadi part-oda last scene)",
        min_value=0.0,
        max_value=5.0,
        value=1.5,
        step=0.5
    )

# FFmpeg path & duration check function
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

def get_video_duration(file_path):
    cmd = [ffmpeg_exe, "-i", file_path]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if match:
        hours, mins, secs = map(float, match.groups())
        return hours * 3600 + mins * 60 + secs
    return 0.0

if uploaded_file is not None:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.caption(f"📁 Uploaded File: **{uploaded_file.name}** ({file_size_mb:.1f} MB)")
    
    if st.button("🚀 Generate Parts (Super Fast)", type="primary"):
        with st.spinner("2-Hour Video fast-ah split aaguthu... Konjam wait pannu bro!"):
            temp_dir = tempfile.mkdtemp()
            input_path = os.path.join(temp_dir, uploaded_file.name)
            
            # Large file-ah memory hang aagama chunk-by-chunk save panrom
            with open(input_path, "wb") as f:
                while True:
                    chunk = uploaded_file.read(8 * 1024 * 1024)  # 8MB chunks
                    if not chunk:
                        break
                    f.write(chunk)
            
            total_duration = get_video_duration(input_path)
            
            if total_duration == 0:
                st.error("Video duration read panna mudiyala. Vera MP4 file try pannu bro.")
            else:
                step = clip_duration - overlap_sec
                clips_times = []
                current_start = 0.0
                
                while current_start < total_duration:
                    current_end = min(current_start + clip_duration, total_duration)
                    clips_times.append((current_start, current_end))
                    if current_end >= total_duration:
                        break
                    current_start += step
                
                total_parts = len(clips_times)
                mins_total = int(total_duration // 60)
                secs_total = int(total_duration % 60)
                st.info(f"Total Length: {mins_total} mins {secs_total} secs | Total Parts: {total_parts} (Overlap: {overlap_sec}s)")
                
                progress_bar = st.progress(0)
                output_files = []
                
                # Direct FFmpeg stream copy (Re-encode illama ultra fast-ah cut aagum)
                for i, (start_time, end_time) in enumerate(clips_times):
                    part_num = i + 1
                    output_filename = f"Part_{part_num:03d}.mp4"  # Part_001, Part_002 nu order-ah varum
                    output_path = os.path.join(temp_dir, output_filename)
                    duration_to_cut = end_time - start_time
                    
                    cmd = [
                        ffmpeg_exe, "-y",
                        "-ss", str(start_time),
                        "-i", input_path,
                        "-t", str(duration_to_cut),
                        "-c", "copy",
                        "-avoid_negative_ts", "make_zero",
                        output_path
                    ]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    
                    output_files.append((output_filename, output_path, round(start_time, 1), round(end_time, 1)))
                    progress_bar.progress((i + 1) / total_parts)
                
                st.success(f"Done! Ellam {total_parts} parts-um {overlap_sec}s overlap-oda ready!")
                
                # ZIP File Creation (STORE mode - already compressed MP4-ah fast-ah pack pannum)
                zip_path = os.path.join(temp_dir, "All_Video_Parts.zip")
                with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_STORED) as zipf:
                    for file_name, file_path, _, _ in output_files:
                        if os.path.exists(file_path):
                            zipf.write(file_path, arcname=file_name)
                
                with open(zip_path, "rb") as zf:
                    st.download_button(
                        label=f"📦 Download All {total_parts} Parts (ZIP)",
                        data=zf,
                        file_name="All_Video_Parts.zip",
                        mime="application/zip"
                    )
                
                st.divider()
                st.subheader("Preview (First 10 Parts)")
                st.caption("200+ videos irundha browser hang aagum, adhanaala first 10 parts mattum preview kaattuthu. Ellam ZIP file-la irukkum!")
                
                for file_name, file_path, s_time, e_time in output_files[:10]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{file_name}** (`{s_time}s` - `{e_time}s`)")
                        st.video(file_path)
                    with col2:
                        with open(file_path, "rb") as vf:
                            st.download_button(
                                label=f"⬇️ {file_name}",
                                data=vf,
                                file_name=file_name,
                                mime="video/mp4",
                                key=file_name
                            )