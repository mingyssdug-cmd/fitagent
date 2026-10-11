const auth = require('../../utils/auth');

Page({
  data: {
    userInfo: {},
  },

  onShow() {
    const userInfo = auth.getUserInfo();
    if (!userInfo) {
      wx.redirectTo({ url: '/pages/login/login' });
      return;
    }
    this.setData({ userInfo });
  },

  // 清空聊天历史
  onClearHistory() {
    wx.showModal({
      title: '提示',
      content: '确定清空聊天历史吗？清空后无法恢复。',
      confirmColor: '#e64340',
      success: (res) => {
        if (res.confirm) {
          const userInfo = auth.getUserInfo();
          const userId = userInfo ? userInfo.user_id : 'anonymous';
          // 用当前用户的 key 清空
          wx.removeStorageSync(`chat_history_${userId}`);
          wx.showToast({ title: '已清空', icon: 'success' });
        }
      },
    });
  },

  // 退出登录
  onLogout() {
    wx.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          auth.clearLogin();
          wx.showToast({ title: '已退出', icon: 'success' });
          setTimeout(() => {
            wx.redirectTo({ url: '/pages/login/login' });
          }, 500);
        }
      },
    });
  },
});