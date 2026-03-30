/**
 * Gamification System - Achievements, Levels, Progress Tracking
 */

class GamificationSystem {
    constructor() {
        this.achievements = [];
        this.progress = this.loadProgress();
        this.setupAchievements();
    }

    loadProgress() {
        const saved = localStorage.getItem('rehabihand_progress');
        return saved ? JSON.parse(saved) : {
            level: 1,
            totalScore: 0,
            totalReps: 0,
            perfectReps: 0,
            gamesPlayed: {},
            unlockedAchievements: [],
            dailyStats: {}
        };
    }

    saveProgress() {
        localStorage.setItem('rehabihand_progress', JSON.stringify(this.progress));
    }

    setupAchievements() {
        this.achievements = [
            {
                id: 'first_rep',
                name: 'First Step',
                description: 'Complete your first repetition',
                icon: '🎯',
                condition: (stats) => stats.totalReps >= 1
            },
            {
                id: 'ten_reps',
                name: 'Getting Started',
                description: 'Complete 10 repetitions',
                icon: '💪',
                condition: (stats) => stats.totalReps >= 10
            },
            {
                id: 'hundred_reps',
                name: 'Century Club',
                description: 'Complete 100 repetitions',
                icon: '🏆',
                condition: (stats) => stats.totalReps >= 100
            },
            {
                id: 'perfect_ten',
                name: 'Perfection',
                description: '10 perfect form reps in a row',
                icon: '✨',
                condition: (stats) => stats.perfectReps >= 10
            },
            {
                id: 'high_score',
                name: 'High Roller',
                description: 'Score 10,000 points',
                icon: '🎮',
                condition: (stats) => stats.totalScore >= 10000
            },
            {
                id: 'all_games',
                name: 'Complete Collection',
                description: 'Play all 5 game modes',
                icon: '🌟',
                condition: (stats) => Object.keys(stats.gamesPlayed).length >= 5
            },
            {
                id: 'streak_seven',
                name: 'Week Warrior',
                description: 'Train for 7 days in a row',
                icon: '🔥',
                condition: (stats) => this.getStreak() >= 7
            }
        ];
    }

    /**
     * Update progress after game session
     */
    updateProgress(gameData) {
        this.progress.totalScore += gameData.score || 0;
        this.progress.totalReps += gameData.reps || 0;
        this.progress.perfectReps += gameData.perfectReps || 0;

        // Track game played
        if (gameData.gameName) {
            if (!this.progress.gamesPlayed[gameData.gameName]) {
                this.progress.gamesPlayed[gameData.gameName] = 0;
            }
            this.progress.gamesPlayed[gameData.gameName]++;
        }

        // Update daily stats
        const today = new Date().toDateString();
        if (!this.progress.dailyStats[today]) {
            this.progress.dailyStats[today] = {
                score: 0,
                reps: 0,
                gamesPlayed: []
            };
        }
        this.progress.dailyStats[today].score += gameData.score || 0;
        this.progress.dailyStats[today].reps += gameData.reps || 0;
        if (gameData.gameName && !this.progress.dailyStats[today].gamesPlayed.includes(gameData.gameName)) {
            this.progress.dailyStats[today].gamesPlayed.push(gameData.gameName);
        }

        // Check for level up
        this.checkLevelUp();

        // Check achievements
        this.checkAchievements();

        // Update UI
        this.updateProgressUI();

        // Save
        this.saveProgress();
    }

    /**
     * Check if player leveled up
     */
    checkLevelUp() {
        const scoreForNextLevel = this.progress.level * 1000;
        if (this.progress.totalScore >= scoreForNextLevel) {
            this.progress.level++;
            this.showLevelUpNotification();
        }
    }

    showLevelUpNotification() {
        const popup = document.getElementById('achievement-popup');
        const title = document.getElementById('achievement-title');
        const desc = document.getElementById('achievement-desc');

        if (popup && title && desc) {
            title.textContent = `Level ${this.progress.level}!`;
            desc.textContent = 'You\'ve leveled up! Keep up the great work!';
            popup.classList.remove('hidden');
            popup.classList.add('show');

            setTimeout(() => {
                popup.classList.remove('show');
                setTimeout(() => popup.classList.add('hidden'), 500);
            }, 3000);
        }
    }

    /**
     * Check for new achievements
     */
    checkAchievements() {
        this.achievements.forEach(achievement => {
            if (!this.progress.unlockedAchievements.includes(achievement.id)) {
                if (achievement.condition(this.progress)) {
                    this.unlockAchievement(achievement);
                }
            }
        });
    }

    unlockAchievement(achievement) {
        this.progress.unlockedAchievements.push(achievement.id);
        this.showAchievementNotification(achievement);
    }

    showAchievementNotification(achievement) {
        const popup = document.getElementById('achievement-popup');
        const title = document.getElementById('achievement-title');
        const desc = document.getElementById('achievement-desc');
        const icon = popup.querySelector('.achievement-icon');

        if (popup && title && desc && icon) {
            icon.textContent = achievement.icon;
            title.textContent = achievement.name;
            desc.textContent = achievement.description;
            popup.classList.remove('hidden');
            popup.classList.add('show');

            setTimeout(() => {
                popup.classList.remove('show');
                setTimeout(() => popup.classList.add('hidden'), 500);
            }, 4000);
        }
    }

    /**
     * Get current training streak
     */
    getStreak() {
        const dates = Object.keys(this.progress.dailyStats).sort().reverse();
        let streak = 0;
        let currentDate = new Date();

        for (let i = 0; i < dates.length; i++) {
            const checkDate = new Date(currentDate);
            checkDate.setDate(checkDate.getDate() - i);
            const dateStr = checkDate.toDateString();

            if (dates.includes(dateStr)) {
                streak++;
            } else {
                break;
            }
        }

        return streak;
    }

    /**
     * Update progress UI elements
     */
    updateProgressUI() {
        // Update level display
        const levelDisplay = document.getElementById('current-level');
        if (levelDisplay) {
            levelDisplay.textContent = this.progress.level;
        }

        // Update total reps
        const repsDisplay = document.getElementById('total-reps');
        if (repsDisplay) {
            repsDisplay.textContent = this.progress.totalReps;
        }

        // Update perfect form count
        const perfectDisplay = document.getElementById('perfect-form');
        if (perfectDisplay) {
            perfectDisplay.textContent = this.progress.perfectReps;
        }

        // Update level progress bar
        const progressBar = document.getElementById('level-progress');
        if (progressBar) {
            const scoreForNextLevel = this.progress.level * 1000;
            const progress = (this.progress.totalScore % 1000) / 10;
            progressBar.style.width = `${progress}%`;
        }
    }

    /**
     * Reset all progress (for testing)
     */
    resetProgress() {
        localStorage.removeItem('rehabihand_progress');
        this.progress = this.loadProgress();
        this.updateProgressUI();
    }
}

window.GamificationSystem = GamificationSystem;
