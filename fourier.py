from statistics import mode
import tkinter
from tkinter import filedialog
from PIL import Image, ImageTk, ImageChops
import numpy as np
from PIL import ImageDraw
from matplotlib import pyplot as plt
import cv2
from tkinter import messagebox

RIGHT_CANVAS = False
def file_select():
  filetype = [("画像ファイル","*.jpg"), ("画像ファイル","*.png")] #拡張子の選択
  file_path = tkinter.filedialog.askopenfilename(filetypes = filetype)
  return file_path

def push_save_button():
  if RIGHT_CANVAS:
    messagebox.showinfo('保存完了', 'mosaiced.jpgとして保存しました')
    pasted_img.save("mosaiced.jpg")

def push_load_button():
  global before_img, b_img
  file_path = file_select()
  before_img = Image.open(file_path).convert('L')
  b_img = ImageTk.PhotoImage(before_img)
  sx = (left_canvas.winfo_width() - b_img.width()) // 2
  sy = (left_canvas.winfo_height() - b_img.height()) // 2
  left_canvas.create_image(
      sx, sy,
      image=b_img,
      anchor=tkinter.NW,
      tag="image"
  )
  
def low_filter(image):
  img = np.array(image, dtype=np.uint8)
  dft = cv2.dft(np.float32(img),flags = cv2.DFT_COMPLEX_OUTPUT) #二次元フーリエ変換
  dft_shift = np.fft.fftshift(dft) #原点シフト
  rows, cols = img.shape
  crow,ccol = int(rows/2) , int(cols/2)
  fil2 = 7 #モザイク度
  mask = np.zeros((rows,cols,2),np.uint8)
  mask[crow-fil2:crow+fil2, ccol-fil2:ccol+fil2] = 1 #周波数フィルタ
  fshift = dft_shift*mask #周波数フィルタリング
  f_ishift = np.fft.ifftshift(fshift) #逆フーリエ変換
  img_back = cv2.idft(f_ishift)
  img_back = cv2.magnitude(img_back[:,:,0],img_back[:,:,1])
  fig, ax = plt.subplots()
  fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
  plt.imshow(img_back, cmap="gray")
  plt.xticks([]), plt.yticks([])
  fig.canvas.draw()
  im = np.array(fig.canvas.renderer.buffer_rgba())
  img = Image.fromarray(im)
  return img

def round(value, min, max):
    ret = value
    if(value < min):
        ret = min
    if(value > max):
        ret = max

    return ret

def img_crop(param):
  x1, y1, x2, y2 = param
  x1 = round(x1, 0, before_img.width)
  x2 = round(x2, 0, before_img.width)
  y1 = round(y1, 0, before_img.height)
  y2 = round(y2, 0, before_img.height)
  if x1 <= x2:
      crop_x1 = x1
      crop_x2 = x2
  else:
      crop_x1 = x2
      crop_x2 = x1
  if y1 <= y2:
      crop_y1 = y1
      crop_y2 = y2
  else:
      crop_y1 = y2
      crop_y2 = y1
  global after_img, a_img, mosaic_img, m_img
  after_img = before_img.crop((crop_x1,crop_y1,crop_x2,crop_y2))
  a_img = ImageTk.PhotoImage(after_img)
  mosaic_img = low_filter(after_img)
  m_img = ImageTk.PhotoImage(mosaic_img)
  orig_x = crop_x2 - crop_x1
  orig_y = crop_y2 - crop_y1
  bg = Image.new("RGBA", mosaic_img.size, mosaic_img.getpixel((0, 0)))
  diff = ImageChops.difference(mosaic_img, bg)
  croprange = diff.convert("RGB").getbbox()
  mosaic_img = mosaic_img.crop(croprange)

  global pasted_img, p_img
  pasted_img = before_img.copy()
  mosaic_img = mosaic_img.resize((orig_x, orig_y))
  pasted_img.paste(mosaic_img, (crop_x1, crop_y1))
  p_img = ImageTk.PhotoImage(pasted_img)
  sx = (right_canvas.winfo_width() - p_img.width()) // 2
  sy = (right_canvas.winfo_height() - p_img.height()) // 2
  global RIGHT_CANVAS
  RIGHT_CANVAS = True
  right_canvas.create_image(
      sx, sy,
      image=p_img,
      anchor=tkinter.NW,
      tag="image"
  )
  
def delete_selection():
  objs = left_canvas.find_withtag("selection_rectangle")
  for obj in objs:
      left_canvas.delete(obj)

pressing = False
selection = None
def button_press(event):
  global pressing
  global selection
  pressing = True
  selection = None
  selection = [
      event.x,
      event.y,
      event.x,
      event.y
  ]

def mouse_motion(event):
  if pressing:
      selection[2] = event.x
      selection[3] = event.y
      delete_selection()
      left_canvas.create_rectangle(
                selection[0],
                selection[1],
                selection[2],
                selection[3],
                outline="red",
                width=1,
                tag="selection_rectangle"
            )

def button_release(event):
  global pressing
  if pressing:
    pressing = False
    selection[2] = event.x
    selection[3] = event.y
    objs = left_canvas.find_withtag("image")
    if len(objs) != 0:
        draw_coord = left_canvas.coords(objs[0])
        x1 = selection[0] - draw_coord[0]
        y1 = selection[1] - draw_coord[1]
        x2 = selection[2] - draw_coord[0]
        y2 = selection[3] - draw_coord[1]
        img_crop((int(x1), int(y1), int(x2), int(y2)))



root = tkinter.Tk()
root.title("モザイク処理")
root.geometry("1200x500")
canvas_width = 500
canvas_height = 500
main_frame = tkinter.Frame(root)
main_frame.pack()
sub_frame = tkinter.Frame(root)
sub_frame.pack()
canvas_frame = tkinter.Frame(main_frame)
canvas_frame.grid(column=1, row=1)
button_frame = tkinter.Frame(main_frame)
button_frame.grid(column=2, row=1)
left_canvas = tkinter.Canvas(
    canvas_frame,
    width=canvas_width,
    height=canvas_height,
    bg="gray",
)
left_canvas.grid(column=1, row=1)
right_canvas = tkinter.Canvas(
    canvas_frame,
    width=canvas_width,
    height=canvas_height,
    bg="gray",
)
right_canvas.grid(column=2, row=1)
load_button = tkinter.Button(button_frame, text="ファイル選択")
load_button.grid(row=1)
save_button = tkinter.Button(button_frame,text="画像保存")
save_button.grid(row=2)
load_button['command'] = push_load_button
save_button['command'] = push_save_button
left_canvas.bind("<ButtonPress>", button_press)
left_canvas.bind("<Motion>", mouse_motion,)
left_canvas.bind("<ButtonRelease>", button_release,)
root.mainloop()
