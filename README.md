# AI Puppetry: Rối Thủy Đình

Điều khiển rối dây bằng tay qua webcam (MediaPipe). Màn hình vuông: nửa trên là camera, nửa dưới là sân khấu, dây chạy từ đầu ngón tay xuống rối. Mất tay thì dây đứt, rối ngã kiểu ragdoll. Tay quay lại thì dây tự nối từ đầu ngón tay xuống rối và kéo rối đứng dậy.

```
assets/   art rối (rig.json + mảnh PNG) và sân khấu, kèm script Python để vẽ lại
web/      web app: Vite + TypeScript + MediaPipe Tasks Vision + Planck.js (vật lý) + Canvas 2D
```

## Cảnh (scene)

| Cảnh | Mở bằng | Rối | Hiệu ứng |
|---|---|---|---|
| Núi tuyết (mặc định) | `http://localhost:5173` | Chiến binh tuyết (thương), vệ binh Streltsy (kiếm) | tuyết rơi, gió lạnh, cờ lều bay, lửa trại, khói, cực quang |
| Thủy đình | `http://localhost:5173/?scene=thuydinh` | Chú Tễu, cô gái áo dài | cờ bay, sóng hồ, cá nhảy, gió, hạc bay |

Thêm hoặc sửa cảnh trong `SCENES` ở `web/src/config.ts`.

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

| Ngón tay | Tay phải của bạn | Tay trái của bạn |
|---|---|---|
| Ngón giữa | Đầu | Đầu |
| Ngón trỏ | Tay trái rối | Tay phải rối |
| Ngón cái | Chân trái rối | Chân phải rối |
| Ngón áp út | Tay phải rối | Tay trái rối |
| Ngón út | Chân phải rối | Chân trái rối |

Trái/phải của rối tính theo phía trên màn hình.

- Di chuyển cả bàn tay: rối di chuyển theo.
- Hai tay: tay trái điều khiển rối bên trái, tay phải điều khiển rối bên phải.
- Phím tắt: `C` camera, `M` chuột, `R` reset, `D` xem collider, `S` âm thanh, `U`/`I` đại chiêu.
- Dây đầu dài cố định (3/10 chiều cao màn hình), dây tay và dây gối chùng thêm một đoạn, tất cả hơi đàn hồi. Đưa tay lên cao thì dây căng và nhấc rối lên, hạ tay xuống thì dây chùng và rối ngồi xuống.

## Đánh nhau

- Vũ khí (thương, kiếm) chạm vào người con rối kia đủ nhanh là một đòn: người bị đánh văng ra sau, dây chùng một nhịp rồi kéo lại, máu bắn ra và loang trên nền.
- Hai vũ khí chạm nhau thì tóe tia lửa.
- Chỉnh trong mục `combat` của `web/src/config.ts`: `minHitSpeed` (tốc độ tối thiểu để tính đòn), `knockback` (lực hất), `staggerTime` (thời gian dây chùng), `cooldown`, `shakePx` (độ rung màn hình). Thêm vũ khí mới bằng cách ghi tên mảnh vào `weapons`.

## Đại chiêu

Cử chỉ: bàn tay hình chữ L (ngón trỏ duỗi, ngón cái duỗi ngang, 3 ngón còn lại co), ngón trỏ chỉ **lên**, rồi lật nhanh cho ngón trỏ chỉ **xuống** trong 0.35 giây. Trong lúc làm cử chỉ, dây của rối bị khóa nên rối không bị giật.

| Nhân vật | Đại chiêu |
|---|---|
| Chiến binh tuyết | Kiếm băng khổng lồ rơi xuống đầu đối thủ (né được). Trúng thì đối thủ vỡ thành từng mảnh văng tứ tung 3 giây, sau đó các mảnh bay về ghép lại thành người và dây nối lại với tay. |
| Vệ binh Streltsy | Kiếm băng bay tới đối thủ từ mọi hướng (trên, hai bên, chéo) trong 4 giây. Đối thủ mất dây suốt 4 giây, mỗi thanh trúng hất văng theo hướng ngẫu nhiên. |

- Hồi chiêu 10 giây, vòng tròn trên đầu mỗi nhân vật cho biết khi nào dùng lại được.
- Test bằng phím: `U` (nhân vật 1), `I` (nhân vật 2).
- Chỉnh trong mục `ult` của `web/src/config.ts`: `gestureWindow` (thời gian lật tay), `angleTolerance`, `cooldown`, thông số từng chiêu.
- Vũ khí có vệt sáng khi vung và hào quang băng (mục `weaponFx`).

## Âm thanh

Âm thanh được tổng hợp bằng Web Audio, không cần file: vung vũ khí, trúng đòn, chạm kiếm, đứt và nối dây, tung chiêu, kiếm rơi, va chạm, mưa kiếm, gió, lửa trại. Phím `S` bật/tắt, âm lượng ở `sound.volume`.

## Chỉnh cảm giác điều khiển

Mọi thông số nằm trong `web/src/config.ts`, ví dụ:
- `rope.lengths.middle`: độ dài dây đầu (ngón giữa) so với chiều cao màn hình.
- `rope.slack`: độ chùng thêm của dây tay (ngón trỏ, áp út) và dây gối (ngón cái, út). Tăng lên thì tay chân rối lỏng hơn.
- `swapHandedness`: đặt `true` nếu webcam của bạn nhận nhầm tay trái và tay phải.
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
python assets/background_snow/gen_background_snow.py
python assets/puppet/chien_binh_tuyet/gen_chien_binh_tuyet.py
python assets/puppet/ve_binh_streltsy/gen_ve_binh_streltsy.py
python assets/make_preview.py
```
Sau đó chạy lại `npm run dev` để web nhận asset mới.
