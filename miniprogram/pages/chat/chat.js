const auth = require('../../utils/auth');
const { BASE_URL } = require('../../utils/request');

const MAX_HISTORY = 50;

/**
 * 获取当前用户的聊天记录存储 key
 * 格式：chat_history_{user_id}
 */
function getHistoryKey() {
  const userInfo = auth.getUserInfo();
  const userId = userInfo ? userInfo.user_id : 'anonymous';
  return `chat_history_${userId}`;
}

Page({
  data: {
    messages: [],
    inputValue: '',
    sending: false,
    canSend: false,
    scrollToId: '',
  },

  onLoad() {
    if (!auth.isLoggedIn()) {
      wx.redirectTo({ url: '/pages/login/login' });
    }
  },

  onShow() {
    if (this.data.sending) return;

    // 用当前用户的 key 读取
    const history = wx.getStorageSync(getHistoryKey()) || [];
    this.setData({ messages: history }, () => this.scrollToBottom());
  },

  onInput(e) {
    const value = e.detail.value;
    this.setData({
      inputValue: value,
      canSend: value.trim().length > 0 && !this.data.sending,
    });
  },

  onSend() {
    const text = this.data.inputValue.trim();
    if (!text || this.data.sending) return;

    const userMsg = { id: Date.now(), role: 'user', content: text };
    const messages = [...this.data.messages, userMsg];
    this.setData({
      messages,
      inputValue: '',
      canSend: false,
      sending: true,
    }, () => this.scrollToBottom());

    this.streamRequest(text, '/api/v1/chat/stream');
  },

  onGeneratePlan() {
    if (this.data.sending) return;

    const userMsg = { id: Date.now(), role: 'user', content: '⚡ 一键生成训练计划' };
    const messages = [...this.data.messages, userMsg];
    this.setData({ messages, sending: true }, () => this.scrollToBottom());

    this.streamRequest('', '/api/v1/plans/generate/stream');
  },

  streamRequest(text, url) {
    const token = auth.getToken();
    let buffer = '';
    let fullContent = '';
    const aiMsgId = Date.now() + 1;

    const aiMsg = { id: aiMsgId, role: 'assistant', content: '', loading: true };
    this.setData({ messages: [...this.data.messages, aiMsg] }, () => this.scrollToBottom());

    const body = url.includes('/chat/') ? { message: text } : {};

    const task = wx.request({
      url: BASE_URL + url,
      method: 'POST',
      header: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token,
      },
      data: body,
      enableChunked: true,
      responseType: 'arraybuffer',
      timeout: 120000,
      success: () => {
        this.finishMessage(aiMsgId, fullContent);
      },
      fail: (err) => {
        this.updateMessage(aiMsgId, '请求失败，请重试', false);
        this.setData({
          sending: false,
          canSend: this.data.inputValue.trim().length > 0,
        });
        wx.showToast({ title: '网络错误', icon: 'none' });
      },
    });

    task.onChunkReceived((res) => {
      const chunkText = new TextDecoder('utf-8').decode(new Uint8Array(res.data));
      buffer += chunkText;

      let idx;
      while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const line = buffer.slice(0, idx).trim();
        buffer = buffer.slice(idx + 2);

        if (line.startsWith('data: ')) {
          const content = line.slice(6);
          if (content === '[DONE]') return;
          if (content.startsWith('[ERROR]')) {
            this.updateMessage(aiMsgId, '错误：' + content.slice(8), false);
            this.setData({ sending: false });
            return;
          }
          fullContent += content;
          this.updateMessage(aiMsgId, fullContent, true);
        }
      }
    });
  },

  updateMessage(id, content, loading) {
    const messages = this.data.messages.map(m =>
      m.id === id ? { ...m, content, loading } : m
    );
    this.setData({ messages }, () => this.scrollToBottom());
  },

  finishMessage(id, content) {
    this.updateMessage(id, content, false);
    this.setData({ sending: false });
    this.saveHistory();
  },

  saveHistory() {
    let messages = this.data.messages;
    if (messages.length > MAX_HISTORY) {
      messages = messages.slice(-MAX_HISTORY);
    }
    // 用当前用户的 key 保存
    wx.setStorageSync(getHistoryKey(), messages);
  },

  scrollToBottom() {
    const messages = this.data.messages;
    if (messages.length === 0) return;
    const lastId = messages[messages.length - 1].id;
    this.setData({ scrollToId: 'msg-' + lastId });
  },
});