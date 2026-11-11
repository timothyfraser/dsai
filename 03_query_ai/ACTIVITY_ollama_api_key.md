# 📌 ACTIVITY

## Set Up Gemini API Key

🕒 *Estimated Time: 5 minutes*

---

## ✅ Your Task

Set up a free **Google Gemini** API key to query a cloud model. This lets you use a larger model that runs on Google's servers instead of your local computer. Ollama's cloud now charges per token, so the course uses Google's free tier.

The free tier may use your prompts to improve Google's products, so send only public or made-up data.

### 🔑 1. Get Your API Key

- [ ] Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) and sign in with a Google account
- [ ] Click **Create API key**
- [ ] Copy the API key immediately
- [ ] Save it somewhere safe temporarily

### 💾 2. Store Your API Key

- [ ] In your project root directory, create a file named `.env` if it doesn't already exist
- [ ] Open the `.env` file in your text editor
- [ ] Add your API key in this format:

```
GEMINI_API_KEY=<your key>
```

- [ ] Save the `.env` file
- [ ] **Important**: Make sure `.env` is listed in your `.gitignore` file so you don't accidentally commit your API key to GitHub

### ✅ 3. Verify Setup

- [ ] Run the example script [`03_ollama_cloud.R`](03_ollama_cloud.R) or [`03_ollama_cloud.py`](03_ollama_cloud.py) to test your API key
- [ ] If the script runs successfully and you see a model response, your API key is configured correctly

---

## 📤 To Submit

- For credit: Upon completion, enter into the **CANVAS** assignment textbox entry a screenshot showing your `.env` file (with the API key line visible, but you can blur the actual key value for security).

---

![](../../docs/images/icons.png)

---

← 🏠 [Back to Top](#ACTIVITY)
