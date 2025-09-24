import React, { useMemo, useState } from 'react';

const sampleQuestions = [
  {
    q: 'Which color scheme is best for a formal evening outfit?',
    options: ['Neon and bright', 'Muted monochrome', 'Random mix'],
    answer: 1,
    info: 'Muted monochrome palettes (black/charcoal/navy) are timeless for evening wear.'
  },
  {
    q: 'What is a good rule of thumb for patterns?',
    options: [
      'Mix as many as possible',
      'Anchor with a solid and add one pattern',
      'Patterns never work'
    ],
    answer: 1,
    info: 'Use one pattern with solids to keep balance and avoid visual noise.'
  },
  {
    q: 'Which layer helps transition from day to night?',
    options: ['Lightweight blazer', 'Flip flops', 'Gym hoodie'],
    answer: 0,
    info: 'A tailored blazer elevates casual looks instantly.'
  }
];

const Quiz = () => {
  const questions = useMemo(() => sampleQuestions, []);
  const [step, setStep] = useState(0);
  const [selected, setSelected] = useState(null);
  const [score, setScore] = useState(0);
  const [done, setDone] = useState(false);

  const current = questions[step];

  const submit = () => {
    if (selected == null) return;
    if (selected === current.answer) setScore((s) => s + 1);
    if (step + 1 < questions.length) {
      setStep((s) => s + 1);
      setSelected(null);
    } else {
      setDone(true);
      try {
        const prev = Number(localStorage.getItem('quiz_best') || 0);
        const best = Math.max(prev, score + (selected === current.answer ? 1 : 0));
        localStorage.setItem('quiz_best', String(best));
      } catch {}
    }
  };

  const reset = () => {
    setStep(0);
    setSelected(null);
    setScore(0);
    setDone(false);
  };

  return (
    <div className="animate-fadeIn">
      <h1 className="text-3xl font-bold text-white mb-6">Quiz</h1>
      <div className="bg-gray-800 rounded-lg p-6 md:p-8">
        {!done ? (
          <div>
            <div className="flex items-center justify-between mb-4 text-gray-300 text-sm">
              <span>Question {step + 1} of {questions.length}</span>
              <span>Score: {score}</span>
            </div>
            <h2 className="text-xl md:text-2xl font-semibold text-white mb-4">{current.q}</h2>
            <div className="grid gap-3">
              {current.options.map((opt, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelected(idx)}
                  className={`text-left px-4 py-3 rounded border transition-colors ${
                    selected === idx
                      ? 'bg-violet-600 border-violet-500 text-white'
                      : 'bg-gray-700 border-gray-600 hover:bg-gray-600 text-gray-200'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
            <div className="mt-5 flex items-center justify-between text-gray-400 text-sm">
              <span>{selected != null ? current.info : 'Select an answer to continue'}</span>
              <button
                onClick={submit}
                className={`px-5 py-2 rounded font-medium transition-colors ${
                  selected == null
                    ? 'bg-gray-600 cursor-not-allowed text-gray-300'
                    : 'bg-violet-600 hover:bg-violet-500 text-white'
                }`}
              >
                {step + 1 === questions.length ? 'Finish' : 'Next'}
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center">
            <div className="text-5xl mb-2">🎉</div>
            <h3 className="text-2xl font-semibold text-white mb-1">Quiz Complete</h3>
            <p className="text-gray-300 mb-4">You scored {score} / {questions.length}</p>
            <button onClick={reset} className="px-5 py-2 rounded bg-violet-600 hover:bg-violet-500 text-white font-medium">
              Retake Quiz
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Quiz;
