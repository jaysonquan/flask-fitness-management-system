# 智谱 AI 视觉识别 API 接入说明

本文档用于配置“图片识别饮食记录”功能，让系统通过智谱 AI 的视觉模型识别一餐中包含的食物、估算克数，并结合食物库计算热量。

## 适用模型

本项目当前适合接入以下智谱视觉模型：

| 模型 | 推荐用途 | 配置值 |
| --- | --- | --- |
| GLM-4.5V | 识别准确性优先，适合正式演示和答辩 | `glm-4.5v` |
| GLM-4V-Flash | 成本优先，适合开发测试和稳定演示 | `glm-4v-flash` |

建议答辩演示优先使用 `glm-4.5v`。如果额度不足或希望降低成本，可以切换为 `glm-4v-flash`。

## 官方接口信息

智谱视觉模型使用对话补全接口：

```text
https://open.bigmodel.cn/api/paas/v4/chat/completions
```

请求头使用 Bearer Token：

```text
Authorization: Bearer 你的智谱APIKey
Content-Type: application/json
```

官方文档参考：

- GLM-4.5V 模型文档：https://docs.bigmodel.cn/cn/guide/models/vlm/glm-4.5v
- GLM-4V-Flash 模型文档：https://docs.bigmodel.cn/cn/guide/models/free/glm-4v-flash
- 对话补全接口文档：https://docs.bigmodel.cn/api-reference

## 本项目配置方式

在项目根目录新建或编辑 `.env` 文件，写入以下内容：

```env
VISION_API_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions
VISION_API_KEY=替换为你的智谱APIKey
VISION_MODEL=glm-4.5v
```

如果要使用 GLM-4V-Flash，将最后一行改成：

```env
VISION_MODEL=glm-4v-flash
```

保存 `.env` 后，必须重启 Flask 服务，配置才会生效。

## 启动与验证步骤

1. 在项目根目录确认 `.env` 已填写智谱配置。
2. 启动服务：

```bash
python app.py
```

如果本地环境不能使用调试重载器，可以使用：

```bash
python -c 'from app import app; app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)'
```

3. 浏览器打开：

```text
http://127.0.0.1:5000/student/login
```

4. 学生登录后进入：

```text
饮食记录 -> 图片识别饮食记录
```

5. 上传餐食图片并点击“开始识别”。

如果接口调用成功，页面会显示：

```text
AI视觉识别成功
```

如果接口失败，页面会显示失败原因，并自动切换到演示回退识别，保证课堂演示不会中断。

## 识别结果格式

系统会要求视觉模型输出 JSON 数组，每个食物包含：

```json
[
  {
    "food_name": "米饭",
    "estimated_grams": 180,
    "confidence": "中",
    "reason": "图片中有一碗白米饭，体积约为普通饭碗一碗"
  }
]
```

字段说明：

| 字段 | 作用 |
| --- | --- |
| `food_name` | 识别出的食物名称 |
| `estimated_grams` | 根据图片估算的克数 |
| `confidence` | 置信度，只使用“高 / 中 / 低” |
| `reason` | 判断依据，方便用户确认和答辩讲解 |

系统收到结果后，会把食物名称匹配到管理员维护的食物库，并按食物库热量计算总热量。

## 测试用请求示例

以下示例用于单独测试智谱接口是否可用。请把 `你的智谱APIKey` 替换成真实 Key，把图片地址替换成可公网访问的图片 URL。

```bash
curl -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
  -H "Authorization: Bearer 你的智谱APIKey" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.5v",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "image_url",
            "image_url": {
              "url": "https://example.com/meal.jpg"
            }
          },
          {
            "type": "text",
            "text": "请识别这张餐食图片中大致包含哪些食物，并估算每种食物的克数。只输出 JSON 数组。"
          }
        ]
      }
    ],
    "temperature": 0.2
  }'
```

测试 GLM-4V-Flash 时，把模型名改为：

```json
"model": "glm-4v-flash"
```

## 常见问题

### 页面提示“尚未配置视觉 API”

检查 `.env` 是否包含这三项：

```env
VISION_API_URL
VISION_API_KEY
VISION_MODEL
```

修改后要重启 Flask 服务。

### 页面提示 401 或 403

通常是 API Key 错误、Key 未启用、额度不足，或账号权限未开通对应模型。

### 页面提示 400

重点检查：

- `VISION_API_URL` 是否为 `https://open.bigmodel.cn/api/paas/v4/chat/completions`
- `VISION_MODEL` 是否写成 `glm-4.5v` 或 `glm-4v-flash`
- 当前 Key 是否有对应模型权限

### 识别结果不准确

可以从三方面改进：

1. 使用更清晰的餐食图片，尽量俯拍或 45 度拍摄。
2. 避免多个食物严重遮挡，最好让主食、肉类、蔬菜边界清楚。
3. 正式演示时优先使用 `glm-4.5v`，它更适合复杂视觉推理。

## 答辩说明口径

可以在演示视频中这样介绍：

```text
系统在饮食记录模块中集成了智谱 AI 视觉模型。学生上传餐食图片后，系统会调用 GLM-4.5V 或 GLM-4V-Flash 识别图片中的食物类别，并估算每种食物的克数。识别结果会进一步匹配后台维护的食物热量库，自动计算本餐热量。为保证系统稳定性，如果视觉接口失败，系统会展示失败原因并回退到演示识别模式，用户仍然可以手动确认和补充食物信息。
```
