import React, { useState } from 'react';
import { useSubmitFeedback } from '../services/queries';
import { motion, AnimatePresence } from 'framer-motion';
import AnimatedPage from '../components/AnimatedPage';
import { Star, MessageSquareHeart, CheckCircle2, ArrowRight, AlertCircle } from 'lucide-react';

const Feedback = () => {
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comments, setComments] = useState('');
  const [localError, setLocalError] = useState(null);
  const [success, setSuccess] = useState(false);

  const { mutateAsync: submitFeedback, isPending: loading } = useSubmitFeedback();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (rating === 0) {
      setLocalError('Please select a rating before submitting.');
      return;
    }

    setLocalError(null);
    try {
      await submitFeedback({ rating, comments });
      setSuccess(true);
    } catch (error) {
      console.error('Failed to submit feedback', error);
      setLocalError('Failed to submit feedback. Please try again.');
    }
  };

  return (
    <AnimatedPage className="relative min-h-[85vh] flex flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      {/* Ambient background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10">
        <motion.div 
          animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.8, 0.5] }}
          transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
          className="absolute top-[20%] left-[20%] w-[40%] h-[40%] rounded-full bg-rose-400/20 blur-[120px]" 
        />
        <motion.div 
          animate={{ scale: [1, 1.3, 1], opacity: [0.4, 0.7, 0.4] }}
          transition={{ duration: 9, repeat: Infinity, ease: "easeInOut", delay: 1 }}
          className="absolute top-[40%] right-[20%] w-[30%] h-[50%] rounded-full bg-orange-400/20 blur-[120px]" 
        />
      </div>

      <div className="w-full max-w-2xl mx-auto space-y-8">
        <div className="text-center space-y-4">
          <motion.div 
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 200, damping: 20 }}
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-rose-100 to-orange-50 text-rose-500 mb-2 shadow-sm border border-white/50 backdrop-blur-sm"
          >
            <MessageSquareHeart className="w-8 h-8" />
          </motion.div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-slate-800 tracking-tight">
            Your Feedback <span className="text-transparent bg-clip-text bg-gradient-to-r from-rose-500 to-orange-500">Matters</span>
          </h1>
          <p className="text-lg text-slate-500 font-medium max-w-xl mx-auto">
            Help us improve our service by rating your experience. Your insights shape GovConnect.
          </p>
        </div>

        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="relative bg-white/60 backdrop-blur-xl border border-white/80 shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-2xl p-8 md:p-10 overflow-hidden text-center"
        >
          <AnimatePresence mode="wait">
            {success ? (
              <motion.div 
                key="success"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ type: "spring", stiffness: 200, damping: 20 }}
                className="py-8 space-y-6"
              >
                <motion.div 
                  initial={{ scale: 0 }} 
                  animate={{ scale: 1 }} 
                  transition={{ type: "spring", delay: 0.2 }}
                  className="mx-auto w-20 h-20 bg-gradient-to-tr from-emerald-100 to-teal-50 rounded-full flex items-center justify-center text-emerald-500 shadow-sm border border-white/50"
                >
                  <CheckCircle2 className="w-10 h-10" />
                </motion.div>
                <div>
                  <h2 className="text-3xl font-extrabold text-slate-800 tracking-tight">Thank You!</h2>
                  <p className="text-slate-500 mt-2 font-medium">Your feedback has been successfully submitted.</p>
                </div>
                <button
                  onClick={() => { setSuccess(false); setRating(0); setComments(''); }}
                  className="mt-8 w-full py-3.5 px-4 bg-white text-slate-700 font-bold rounded-xl border border-slate-200 shadow-sm hover:bg-slate-50 hover:shadow transition-all duration-200 active:scale-[0.98]"
                >
                  Submit Another Response
                </button>
              </motion.div>
            ) : (
              <motion.form 
                key="form"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                onSubmit={handleSubmit} 
                className="space-y-8"
              >
                {localError && (
                  <motion.div 
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-rose-50/90 backdrop-blur-sm text-rose-600 p-4 rounded-xl text-center font-medium border border-rose-100 flex items-center justify-center gap-2 shadow-sm"
                  >
                    <AlertCircle className="w-5 h-5" />
                    {localError}
                  </motion.div>
                )}

                {/* Star Rating Section */}
                <div className="space-y-5 bg-white/50 p-6 rounded-2xl border border-white/60 shadow-inner">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Rate your experience</label>
                  <div className="flex justify-center gap-3">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <motion.button
                        type="button"
                        key={star}
                        whileHover={{ scale: 1.25 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={() => setRating(star)}
                        onMouseEnter={() => setHoverRating(star)}
                        onMouseLeave={() => setHoverRating(0)}
                        className="p-1 focus:outline-none"
                      >
                        <Star 
                          className={`w-12 h-12 transition-all duration-300 drop-shadow-sm ${
                            (hoverRating || rating) >= star 
                              ? 'fill-amber-400 text-amber-400 scale-110' 
                              : 'text-slate-200 fill-slate-50'
                          }`} 
                        />
                      </motion.button>
                    ))}
                  </div>
                </div>

                {/* Comments Section */}
                <div className="space-y-1.5 text-left group">
                  <label className="text-sm font-semibold text-slate-700 ml-1 group-focus-within:text-rose-500 transition-colors">
                    Additional Comments <span className="text-slate-400 font-normal">(Optional)</span>
                  </label>
                  <textarea
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    placeholder="Tell us what you liked or how we can improve..."
                    rows="4"
                    className="w-full px-4 py-3.5 bg-white/80 border border-slate-200 rounded-xl focus:ring-4 focus:ring-rose-500/10 focus:border-rose-400 outline-none transition-all duration-300 shadow-sm hover:bg-white placeholder:text-slate-400 text-slate-800 font-medium resize-none"
                  ></textarea>
                </div>

                <motion.button 
                  type="submit" 
                  whileTap={{ scale: rating === 0 ? 1 : 0.98 }}
                  disabled={rating === 0 || loading}
                  className={`group w-full flex items-center justify-center gap-2 py-4 mt-8 font-bold rounded-xl shadow-lg transition-all duration-300 ${
                    rating === 0 
                      ? 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none' 
                      : loading 
                        ? 'bg-gradient-to-r from-rose-500 to-orange-500 text-white opacity-70 cursor-not-allowed'
                        : 'bg-gradient-to-r from-rose-500 to-orange-500 text-white shadow-rose-500/25 hover:shadow-xl hover:shadow-rose-500/40 hover:-translate-y-0.5'
                  }`}
                >
                  {loading ? (
                    <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      Submit Feedback
                      <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300 opacity-80" />
                    </>
                  )}
                </motion.button>
              </motion.form>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </AnimatedPage>
  );
};

export default Feedback;
