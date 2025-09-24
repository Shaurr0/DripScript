import React, { createContext, useContext, useReducer, useEffect } from 'react';

const GameContext = createContext();

const initialState = {
  totalPoints: 0,
  level: 1,
  badges: [],
  achievements: [],
  wardrobe: [],
  quizzes: [],
  challenges: [],
  recommendations: [],
};

const gameReducer = (state, action) => {
  switch (action.type) {
    case 'LOAD_STATE':
      return { ...state, ...action.payload };
    
    case 'ADD_POINTS':
      const newTotalPoints = state.totalPoints + action.payload;
      const newLevel = Math.floor(newTotalPoints / 100) + 1;
      return {
        ...state,
        totalPoints: newTotalPoints,
        level: newLevel,
      };
    
    case 'ADD_BADGE':
      if (state.badges.some(badge => badge.id === action.payload.id)) {
        return state;
      }
      return {
        ...state,
        badges: [...state.badges, action.payload],
        achievements: [...state.achievements, {
          id: Date.now(),
          type: 'badge',
          message: `Unlocked badge: ${action.payload.name}`,
          timestamp: new Date().toISOString(),
        }],
      };
    
    case 'ADD_WARDROBE_ITEM':
      return {
        ...state,
        wardrobe: [...state.wardrobe, action.payload],
      };
    
    case 'ADD_QUIZ_RESULT':
      return {
        ...state,
        quizzes: [...state.quizzes, action.payload],
      };
    
    case 'ADD_RECOMMENDATION':
      return {
        ...state,
        recommendations: [...state.recommendations, action.payload],
      };
    
    case 'COMPLETE_CHALLENGE':
      return {
        ...state,
        challenges: state.challenges.map(challenge =>
          challenge.id === action.payload.id
            ? { ...challenge, completed: true }
            : challenge
        ),
      };
    
    default:
      return state;
  }
};

// Badge definitions
const badges = {
  getting_started: {
    id: 'getting_started',
    name: 'Getting Started',
    description: 'Upload your first item',
    icon: '🎯',
    condition: (state) => state.wardrobe.length >= 1,
  },
  wardrobe_builder: {
    id: 'wardrobe_builder',
    name: 'Wardrobe Builder',
    description: 'Upload 10 items',
    icon: '👔',
    condition: (state) => state.wardrobe.length >= 10,
  },
  fashion_collector: {
    id: 'fashion_collector',
    name: 'Fashion Collector',
    description: 'Upload 25 items',
    icon: '🏆',
    condition: (state) => state.wardrobe.length >= 25,
  },
  style_explorer: {
    id: 'style_explorer',
    name: 'Style Explorer',
    description: 'Complete your first quiz',
    icon: '🧠',
    condition: (state) => state.quizzes.length >= 1,
  },
  style_expert: {
    id: 'style_expert',
    name: 'Style Expert',
    description: 'Complete 5 quizzes',
    icon: '✨',
    condition: (state) => state.quizzes.length >= 5,
  },
  recommendation_seeker: {
    id: 'recommendation_seeker',
    name: 'Recommendation Seeker',
    description: 'Get your first recommendation',
    icon: '🤖',
    condition: (state) => state.recommendations.length >= 1,
  },
};

export const useGame = () => {
  const context = useContext(GameContext);
  if (!context) {
    throw new Error('useGame must be used within a GameProvider');
  }
  return context;
};

export const GameProvider = ({ children }) => {
  const [state, dispatch] = useReducer(gameReducer, initialState);

  // Load state from localStorage on mount
  useEffect(() => {
    const savedState = localStorage.getItem('fitcheck-game-state');
    if (savedState) {
      dispatch({ type: 'LOAD_STATE', payload: JSON.parse(savedState) });
    }
  }, []);

  // Save state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('fitcheck-game-state', JSON.stringify(state));
  }, [state]);

  // Check for new badges whenever state changes
  useEffect(() => {
    Object.values(badges).forEach(badge => {
      if (badge.condition(state) && !state.badges.some(b => b.id === badge.id)) {
        dispatch({ type: 'ADD_BADGE', payload: badge });
      }
    });
  }, [state]);

  const actions = {
    addPoints: (points) => dispatch({ type: 'ADD_POINTS', payload: points }),
    addWardrobeItem: (item) => {
      dispatch({ type: 'ADD_WARDROBE_ITEM', payload: item });
      actions.addPoints(10); // Points for uploading
    },
    addQuizResult: (result) => {
      dispatch({ type: 'ADD_QUIZ_RESULT', payload: result });
      actions.addPoints(25); // Points for completing quiz
    },
    addRecommendation: (recommendation) => {
      dispatch({ type: 'ADD_RECOMMENDATION', payload: recommendation });
      actions.addPoints(5); // Points for getting recommendation
    },
    completeChallenge: (challenge) => {
      dispatch({ type: 'COMPLETE_CHALLENGE', payload: challenge });
      actions.addPoints(50); // Points for completing challenge
    },
  };

  return (
    <GameContext.Provider value={{ state, ...actions }}>
      {children}
    </GameContext.Provider>
  );
};