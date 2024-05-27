#include <Arduino.h>
#include <WiFi.h>
#include "esp_camera.h"
#include "fd_forward.h"  // Face detection header
#include "fr_forward.h"  // Face recognition header
#include "esp_log.h"

const char* ssid = "Meda";
const char* password = "bojananikola";

String serverName = "192.168.0.29";
String serverPath = "/upload";
const int serverPort = 5000;

WiFiClient client;

// CAMERA_MODEL_AI_THINKER
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

const int timerInterval = 1000;
unsigned long previousMillis = 0;
mtmn_config_t mtmn_config = {0};

void setup() {
  Serial.begin(115200);

  WiFi.mode(WIFI_STA);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);  
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(500);
  }
  Serial.println();
  Serial.print("ESP32-CAM IP Address: ");
  Serial.println(WiFi.localIP());

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 16000000;
  config.pixel_format = PIXFORMAT_JPEG; // Use JPEG for sending photos

  if (psramFound()) {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_CIF;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  mtmn_config = mtmn_init_config();
  
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    delay(1000);
    ESP.restart();
  }
}

void loop() {
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= timerInterval) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) {
      Serial.printf("Captured image: %d x %d, length: %d\n", fb->width, fb->height, fb->len);
      if (faceDetected(fb)) {
        sendPhoto(fb);
      }
      esp_camera_fb_return(fb);
    } else {
      Serial.println("Camera capture failed");
    }
    previousMillis = currentMillis;
  }
}

bool faceDetected(camera_fb_t *fb) {
  dl_matrix3du_t *image_matrix = dl_matrix3du_alloc(1, fb->width, fb->height, 3);
  if (!image_matrix) {
    Serial.println("dl_matrix3du_alloc failed");
    return false;
  }

  fmt2rgb888(fb->buf, fb->len, fb->format, image_matrix->item);

  box_array_t *faces = face_detect(image_matrix, &mtmn_config);

  if (faces) {
    Serial.printf("Faces detected: %d\n", faces->len);
  } else {
    Serial.println("No faces detected");
  }

  bool detected = faces && faces->len > 0;

  if (faces) {
    dl_lib_free(faces->score);
    dl_lib_free(faces->box);
    dl_lib_free(faces->landmark);
    dl_lib_free(faces);
  }

  dl_matrix3du_free(image_matrix);
  return detected;
}

void sendPhoto(camera_fb_t *fb) {
  String getAll;
  String getBody;

  Serial.println("Connecting to server: " + serverName);
  
  if (client.connect(serverName.c_str(), serverPort)) {
    Serial.println("Connection successful!");    

    String camera_id = "esp32-2";

    String head = "--Nile\r\n"
                  "Content-Disposition: form-data; name=\"camera_id\"\r\n\r\n" 
                  + camera_id + "\r\n"
                  "--Nile\r\n"
                  "Content-Disposition: form-data; name=\"image\"; filename=\"esp32-cam.jpg\"\r\n"
                  "Content-Type: image/jpeg\r\n\r\n";
    String tail = "\r\n--Nile--\r\n";

    uint32_t imageLen = fb->len;
    uint32_t extraLen = head.length() + tail.length();
    uint32_t totalLen = imageLen + extraLen;
  
    client.println("POST " + serverPath + " HTTP/1.1");
    client.println("Host: " + serverName);
    client.println("Content-Length: " + String(totalLen));
    client.println("Content-Type: multipart/form-data; boundary=Nile");
    client.println();
    client.print(head);
  
    uint8_t *fbBuf = fb->buf;
    size_t fbLen = fb->len;
    for (size_t n = 0; n < fbLen; n += 1024) {
      if (n + 1024 < fbLen) {
        client.write(fbBuf, 1024);
        fbBuf += 1024;
      } else if (fbLen % 1024 > 0) {
        size_t remainder = fbLen % 1024;
        client.write(fbBuf, remainder);
      }
    }   
    client.print(tail);
    
    int timeoutTimer = 10000;
    long startTimer = millis();
    boolean state = false;
    
    while ((startTimer + timeoutTimer) > millis()) {
      Serial.print(".");
      delay(100);      
      while (client.available()) {
        char c = client.read();
        if (c == '\n') {
          if (getAll.length() == 0) {
            state = true;
          }
          getAll = "";
        } else if (c != '\r') {
          getAll += String(c);
        }
        if (state == true) {
          getBody += String(c);
        }
        startTimer = millis();
      }
      if (getBody.length() > 0) {
        break;
      }
    }
    Serial.println();
    client.stop();
    Serial.println(getBody);
  } else {
    Serial.println("Connection to " + serverName + " failed.");
  }
}
