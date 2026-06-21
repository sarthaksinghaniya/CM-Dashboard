import React, { useState, useEffect, useRef } from 'react';
import { getSocket } from '../services/socket';
import { Bell, X, FileText, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const NotificationBell = () => {
  const [notifications, setNotifications] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    const handleNewComplaint = (data) => {
      const notif = {
        id: Date.now(),
        type: 'newComplaint',
        message: `New ${data.priority} complaint: ${data.ticket_id}`,
        ticket_id: data.ticket_id,
        time: new Date(),
        read: false,
      };
      setNotifications((prev) => [notif, ...prev].slice(0, 20));
      setUnreadCount((prev) => prev + 1);
    };

    const handleStatusUpdated = (data) => {
      const notif = {
        id: Date.now(),
        type: 'statusUpdated',
        message: `Complaint ${data.ticket_id} → ${data.status}`,
        ticket_id: data.ticket_id,
        time: new Date(),
        read: false,
      };
      setNotifications((prev) => [notif, ...prev].slice(0, 20));
      setUnreadCount((prev) => prev + 1);
    };

    socket.on('newComplaint', handleNewComplaint);
    socket.on('statusUpdated', handleStatusUpdated);

    return () => {
      socket.off('newComplaint', handleNewComplaint);
      socket.off('statusUpdated', handleStatusUpdated);
    };
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    setUnreadCount(0);
  };

  const clearAll = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  const timeAgo = (date) => {
    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) markAllRead();
        }}
        className="relative p-2 text-slate-400 hover:text-slate-600 hover:bg-white rounded-full transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 shadow-sm border border-transparent hover:border-slate-200/60"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <motion.span
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center bg-rose-500 text-white text-[10px] font-bold rounded-full border-2 border-white px-1"
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </motion.span>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.96 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-xl border border-slate-200/60 overflow-hidden z-50"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-800">Notifications</h3>
              <div className="flex items-center gap-2">
                {notifications.length > 0 && (
                  <button
                    onClick={clearAll}
                    className="text-xs font-medium text-slate-400 hover:text-rose-500 transition-colors"
                  >
                    Clear all
                  </button>
                )}
              </div>
            </div>

            {/* Body */}
            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <div className="py-10 text-center">
                  <Bell className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                  <p className="text-sm text-slate-400 font-medium">No notifications yet</p>
                </div>
              ) : (
                notifications.map((notif) => (
                  <div
                    key={notif.id}
                    className={`flex items-start gap-3 px-4 py-3 border-b border-slate-50 transition-colors hover:bg-slate-50/80 ${
                      !notif.read ? 'bg-blue-50/40' : ''
                    }`}
                  >
                    <div
                      className={`mt-0.5 w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        notif.type === 'newComplaint'
                          ? 'bg-indigo-100 text-indigo-600'
                          : 'bg-emerald-100 text-emerald-600'
                      }`}
                    >
                      {notif.type === 'newComplaint' ? (
                        <FileText className="w-4 h-4" />
                      ) : (
                        <RefreshCw className="w-4 h-4" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-700 leading-snug">
                        {notif.message}
                      </p>
                      <p className="text-xs text-slate-400 mt-0.5">{timeAgo(notif.time)}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default NotificationBell;
