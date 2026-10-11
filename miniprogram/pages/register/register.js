const { request } = require('../../utils/request');

Page({
  data: {
    name: '',
    phone: '',
    password: '',
    confirmPassword: '',
    canSubmit: false,
    loading: false,
  },

  onNameInput(e) {
    this.setData({ name: e.detail.value }, () => this.checkCanSubmit());
  },

  onPhoneInput(e) {
    this.setData({ phone: e.detail.value }, () => this.checkCanSubmit());
  },

  onPasswordInput(e) {
    this.setData({ password: e.detail.value }, () => this.checkCanSubmit());
  },

  onConfirmPasswordInput(e) {
    this.setData({ confirmPassword: e.detail.value }, () => this.checkCanSubmit());
  },

  checkCanSubmit() {
    const { name, phone, password, confirmPassword } = this.data;
    const ok =
      name.trim().length > 0 &&
      phone.length === 11 &&
      password.length >= 6 &&
      password === confirmPassword;
    this.setData({ canSubmit: ok });
  },

  async onRegister() {
    const { name, phone, password, confirmPassword } = this.data;

    // 前端校验
    if (!name.trim()) {
      wx.showToast({ title: '请输入姓名', icon: 'none' });
      return;
    }
    if (!/^1\d{10}$/.test(phone)) {
      wx.showToast({ title: '手机号格式不正确', icon: 'none' });
      return;
    }
    if (password.length < 6) {
      wx.showToast({ title: '密码不少于 6 位', icon: 'none' });
      return;
    }
    if (password !== confirmPassword) {
      wx.showToast({ title: '两次密码不一致', icon: 'none' });
      return;
    }

    this.setData({ loading: true });
    wx.showLoading({ title: '注册中...' });

    try {
      const res = await request('/api/v1/auth/register', {
        name: name.trim(),
        phone,
        password,
      });

      if (res.code !== 0) {
        throw new Error(res.message || '注册失败');
      }

      wx.hideLoading();
      wx.showToast({ title: '注册成功', icon: 'success' });

      // 返回登录页
      setTimeout(() => {
        wx.navigateBack();
      }, 800);

    } catch (err) {
      wx.hideLoading();
      wx.showToast({ title: err.message || '注册失败', icon: 'none' });
      console.error('register error:', err);
    } finally {
      this.setData({ loading: false });
    }
  },

  goToLogin() {
    wx.navigateBack();
  },
});