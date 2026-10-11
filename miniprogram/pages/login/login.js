const { request } = require('../../utils/request');
const auth = require('../../utils/auth');

Page({
  data: {
    phone: '',
    password: '',
    canSubmit: false,
    loading: false,
  },

  onPhoneInput(e) {
    this.setData({ phone: e.detail.value }, () => this.checkCanSubmit());
  },

  onPasswordInput(e) {
    this.setData({ password: e.detail.value }, () => this.checkCanSubmit());
  },

  checkCanSubmit() {
    const { phone, password } = this.data;
    const ok = phone.length === 11 && password.length >= 6;
    this.setData({ canSubmit: ok });
  },

  async onLogin() {
    const { phone, password } = this.data;

    // 前端基础校验
    if (!/^1\d{10}$/.test(phone)) {
      wx.showToast({ title: '手机号格式不正确', icon: 'none' });
      return;
    }
    if (password.length < 6) {
      wx.showToast({ title: '密码不少于 6 位', icon: 'none' });
      return;
    }

    this.setData({ loading: true });
    wx.showLoading({ title: '登录中...' });

    try {
      const res = await request('/api/v1/auth/login', { phone, password });

      if (res.code !== 0) {
        throw new Error(res.message || '登录失败');
      }

      // 保存登录态
      auth.setLogin(res.data.token, {
        user_id: res.data.user_id,
        name: res.data.name,
        phone: phone,
      });

      wx.hideLoading();
      wx.showToast({ title: '登录成功', icon: 'success' });

      // 跳转到聊天页（tabBar 页用 switchTab）
      setTimeout(() => {
        wx.switchTab({ url: '/pages/chat/chat' });
      }, 800);

    } catch (err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '登录失败', icon: 'none' });
      console.error('login error:', err);
    } finally {
      this.setData({ loading: false });
    }
  },

  goToRegister() {
    wx.navigateTo({ url: '/pages/register/register' });
  },
});