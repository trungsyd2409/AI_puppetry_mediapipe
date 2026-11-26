# Assets: rối + sân khấu

```
assets/
  preview.html            mở bằng trình duyệt: 2 rối trên sân khấu, thanh trượt khớp, nút "Lắc lư"
  make_preview.py         tạo lại preview.html sau khi sửa rig
  puppet/
    puppet_lib.py         hàm vẽ dùng chung + xuất mảnh, rig.json
    teu/                  Chú Tễu (10 mảnh)
    co_gai/               Cô gái áo dài, nón lá (13 mảnh: thêm hair, flap_front, flap_back)
  background/
    stage_bg.png|svg      nền thủy đình (vẽ trước rối)
    stage_fg.png|svg      nước + sen phía trước (vẽ sau rối)
    stage.json            floorY (mặt sàn), stageX, puppetHeight gợi ý
```

## rig.json
- `parts[]`: `id`, `parent`, `z` (thứ tự vẽ), `origin` (góc trên trái khi đứng nghỉ),
  `size`, `pivot` (điểm khớp trong mảnh), `limitDeg` (giới hạn góc so với cha), `png`, `svg`.
- `strings[]`: điểm buộc dây trên rối + ngón tay MediaPipe (`mpLandmark`: 4 cái, 8 trỏ, 12 giữa, 16 áp út, 20 út).
- `feetY`: đáy bàn chân, dùng để đặt rối lên `floorY` của sân khấu.
- Đơn vị: 1 unit = 2 px trong PNG, y hướng xuống, `_L` = bên trái người xem.

## Vẽ lại
Cần `rsvg-convert` và Pillow.
```
python puppet/teu/gen_teu.py
python puppet/co_gai/gen_co_gai.py
python background/gen_background.py
python make_preview.py
```
