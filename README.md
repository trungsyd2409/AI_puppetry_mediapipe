# AI Puppetry: Rối Thủy Đình

Điều khiển rối dây bằng tay qua webcam (MediaPipe). Màn hình vuông: nửa trên là camera, nửa dưới là sân khấu, dây chạy từ đầu ngón tay xuống rối. Mất tay thì dây đứt, rối ngã kiểu ragdoll. Tay quay lại thì dây tự nối từ đầu ngón tay xuống rối và kéo rối đứng dậy.

```
assets/   art rối (rig.json + mảnh PNG) và sân khấu, kèm script Python để vẽ lại
web/      web app: Vite + TypeScript + MediaPipe Tasks Vision + Planck.js (vật lý) + Canvas 2D
```

## Chạy trên máy (Windows)

1. Cài **Node.js LTS** (bản 20 hoặc 22) từ https://nodejs.org, rồi mở lại terminal.
2. Mở PowerShell trong folder project:
   ```
   cd web
   npm install
   npm run dev
   ```
   `npm run dev` tự chép asset từ `assets/` sang `web/public/`, chép file wasm của MediaPipe và tải model `hand_landmarker.task` (chỉ lần đầu).
3. Mở http://localhost:5173 bằng Chrome hoặc Edge, bấm **Bật camera** và cho phép quyền camera.
4. Không có camera thì bấm **Dùng chuột (test)**: giữ chuột trái trên sân khấu để làm "tay", giữ phím 1 đến 5 để nhấc từng ngón, thả chuột để rối ngã.

## Cách điều khiển

| Ngón tay | Dây nối tới |
|---|---|
| Ngón giữa | Đầu |
| Ngón trỏ | Tay bên trái màn hình |
| Ngón áp út | Tay bên phải màn hình |
| Ngón cái | Gối trái |
| Ngón út | Gối phải |

- Di chuyển cả bàn tay: rối di chuyển theo.
- Hai tay: tay trái điều khiển rối bên trái, tay phải điều khiển rối bên phải.
- Phím tắt: `C` camera, `M` chuột, `R` reset, `D` xem collider.
- Dây có chiều dài cố định (mặc định bằng nửa chiều cao màn hình), hơi đàn hồi. Đưa tay lên cao thì dây căng và nhấc rối lên, hạ tay xuống thì dây chùng và rối ngồi xuống.

## Chỉnh cảm giác điều khiển

Mọi thông số nằm trong `web/src/config.ts`, ví dụ:
- `rope.lengthOfScreen`: độ dài dây so với chiều cao màn hình (0.5 = một nửa). Giảm xuống 0.4 nếu bạn hay để tay ở giữa khung camera.
- `rope.omega`, `rope.limbOmega`: độ cứng của dây. Số lớn thì dây ít giãn hơn.
- `rope.attachedDamping`: lực cản không khí khi rối treo, giúp rối bớt đung đưa.
- `loseAfter`, `growTime`, `standTime`: thời gian chờ trước khi ngã, thời gian dây mọc, thời gian đứng dậy.
- `view`: kích thước màn vuông, chiều cao phần camera, phần sân khấu được cắt từ đâu.
- `puppetHeight`: độ cao rối trên sân khấu.
- `ambience`: cá nhảy, chim bay, gió thổi bao lâu một lần, gió đẩy rối mạnh hay nhẹ.

## Nhúng vào website

```
cd web
npm run build
```
Upload folder `web/dist/` lên một host có **HTTPS** (GitHub Pages, Netlify, Vercel...). Nhúng bằng iframe, nhớ có `allow="camera"`:

```html
<iframe src="https://your-site/puppetry/" width="800" height="860" allow="camera; fullscreen" style="border:0"></iframe>
```

Trình duyệt chỉ cho dùng camera trên `https://` hoặc `localhost`. Toàn bộ xử lý chạy trên máy người xem, video không gửi lên server.

## Vẽ lại art (không bắt buộc)

Cần Python, Pillow và `rsvg-convert` (trên Windows dễ nhất là chạy trong WSL):
```
python assets/puppet/teu/gen_teu.py
python assets/puppet/co_gai/gen_co_gai.py
python assets/background/gen_background.py
python assets/background/gen_props.py
python assets/make_preview.py
```
Sau đó chạy lại `npm run dev` để web nhận asset mới.
