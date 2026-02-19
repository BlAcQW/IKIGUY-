import { motion } from "framer-motion";
import { Trophy, Award, Star, Lock, ArrowLeft, BookOpen, Users, Heart, Sparkles, Gift } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { MainNavigation } from "@/components/navigation/MainNavigation";

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon_name: string;
  points_reward: number;
  coins_reward?: number;
  rarity: "common" | "rare" | "epic" | "legendary";
  category: string;
  unlocked: boolean;
  unlocked_at?: string;
  progress: number;
  progress_target: number;
}

const rarityColors = {
  common: "bg-gray-500",
  rare: "bg-blue-500",
  epic: "bg-purple-500",
  legendary: "bg-yellow-500",
};

const rarityGradients = {
  common: "from-gray-400 to-gray-600",
  rare: "from-blue-400 to-blue-600",
  epic: "from-purple-400 to-purple-600",
  legendary: "from-yellow-400 to-yellow-600",
};

const categoryIcons: Record<string, any> = {
  reading: BookOpen,
  engagement: Heart,
  social: Users,
  spiritual: Sparkles,
  special: Gift,
};

const Achievements = () => {
  const navigate = useNavigate();

  // Fetch all achievements
  const { data: achievements = [], isLoading } = useQuery({
    queryKey: ["achievements"],
    queryFn: async () => {
      const response = await apiClient.getAchievements();
      return response as Achievement[];
    },
  });

  // Group achievements by category
  const groupedAchievements = achievements.reduce((acc, achievement) => {
    const category = achievement.category || "General";
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(achievement);
    return acc;
  }, {} as Record<string, Achievement[]>);

  const totalAchievements = achievements.length;
  const unlockedAchievements = achievements.filter((a) => a.unlocked).length;
  const totalPoints = achievements
    .filter((a) => a.unlocked)
    .reduce((sum, a) => sum + a.points_reward, 0);

  return (
    <div className="min-h-screen bg-background">
      <MainNavigation />

      <main className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate("/profile")}
            className="gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Profile
          </Button>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          {/* Stats Card */}
          <div className="bg-gradient-to-br from-secondary/20 to-accent/20 rounded-2xl p-8 border border-border">
            <h1 className="text-3xl font-serif font-bold text-foreground mb-2">
              Your Achievements
            </h1>
            <p className="text-muted-foreground mb-6">
              Track your spiritual journey and unlock rewards
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-background/50 rounded-xl p-4 backdrop-blur-sm">
                <div className="flex items-center gap-3 mb-2">
                  <Trophy className="w-5 h-5 text-yellow-500" />
                  <span className="text-sm text-muted-foreground">Unlocked</span>
                </div>
                <div className="text-3xl font-bold text-foreground">
                  {unlockedAchievements} / {totalAchievements}
                </div>
                <div className="mt-2 h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-secondary to-accent"
                    style={{
                      width: `${(unlockedAchievements / totalAchievements) * 100}%`,
                    }}
                  />
                </div>
              </div>

              <div className="bg-background/50 rounded-xl p-4 backdrop-blur-sm">
                <div className="flex items-center gap-3 mb-2">
                  <Star className="w-5 h-5 text-secondary" />
                  <span className="text-sm text-muted-foreground">Total Points</span>
                </div>
                <div className="text-3xl font-bold text-foreground">{totalPoints}</div>
              </div>

              <div className="bg-background/50 rounded-xl p-4 backdrop-blur-sm">
                <div className="flex items-center gap-3 mb-2">
                  <Award className="w-5 h-5 text-accent" />
                  <span className="text-sm text-muted-foreground">Completion</span>
                </div>
                <div className="text-3xl font-bold text-foreground">
                  {totalAchievements > 0
                    ? Math.round((unlockedAchievements / totalAchievements) * 100)
                    : 0}
                  %
                </div>
              </div>
            </div>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-secondary border-t-transparent" />
              <p className="mt-4 text-muted-foreground">Loading achievements...</p>
            </div>
          )}

          {/* Achievement Categories */}
          {!isLoading && Object.entries(groupedAchievements).map(([category, categoryAchievements]) => {
            const CategoryIcon = categoryIcons[category.toLowerCase()] || Trophy;
            return (
              <div key={category} className="space-y-4">
                <h2 className="text-2xl font-serif font-bold text-foreground flex items-center gap-3">
                  <CategoryIcon className="w-7 h-7 text-secondary" />
                  <span className="capitalize">{category}</span>
                  <span className="text-sm text-muted-foreground font-normal">
                    ({categoryAchievements.filter((a) => a.unlocked).length} /{" "}
                    {categoryAchievements.length})
                  </span>
                </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {categoryAchievements.map((achievement) => (
                  <motion.div
                    key={achievement.id}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    whileHover={{ scale: 1.02 }}
                    className={`relative rounded-xl p-6 border transition-all ${
                      achievement.unlocked
                        ? "bg-card border-border shadow-sm hover:shadow-md"
                        : "bg-muted/50 border-muted opacity-60"
                    }`}
                  >
                    {/* Rarity Badge */}
                    <div
                      className={`absolute top-3 right-3 w-2 h-2 rounded-full ${
                        rarityColors[achievement.rarity]
                      }`}
                      title={achievement.rarity.charAt(0).toUpperCase() + achievement.rarity.slice(1)}
                    />

                    {/* Icon */}
                    <div
                      className={`w-16 h-16 rounded-full mb-4 flex items-center justify-center ${
                        achievement.unlocked
                          ? `bg-gradient-to-br ${rarityGradients[achievement.rarity]}`
                          : "bg-muted"
                      }`}
                    >
                      {achievement.unlocked ? (
                        <span className="text-3xl">{achievement.icon_name}</span>
                      ) : (
                        <Lock className="w-8 h-8 text-muted-foreground" />
                      )}
                    </div>

                    {/* Content */}
                    <h3 className="font-semibold text-lg text-foreground mb-2">
                      {achievement.name}
                    </h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      {achievement.description}
                    </p>

                    {/* Footer */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Star className="w-4 h-4 text-yellow-500" />
                        <span className="text-sm font-medium text-foreground">
                          {achievement.points_reward} pts
                        </span>
                        {achievement.coins_reward && achievement.coins_reward > 0 && (
                          <span className="text-sm text-yellow-600">
                            + {achievement.coins_reward} 🪙
                          </span>
                        )}
                      </div>

                      {achievement.unlocked && achievement.unlocked_at && (
                        <span className="text-xs text-muted-foreground">
                          {new Date(achievement.unlocked_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>

                    {/* Progress Bar (if applicable) */}
                    {!achievement.unlocked && achievement.progress_target > 1 && (
                      <div className="mt-4">
                        <div className="flex justify-between text-xs text-muted-foreground mb-1">
                          <span>Progress</span>
                          <span>
                            {achievement.progress} / {achievement.progress_target}
                          </span>
                        </div>
                        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-secondary to-accent"
                            style={{
                              width: `${Math.min((achievement.progress / achievement.progress_target) * 100, 100)}%`,
                            }}
                          />
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            </div>
            );
          })}

          {/* Empty State */}
          {!isLoading && achievements.length === 0 && (
            <div className="text-center py-12">
              <Trophy className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-foreground mb-2">
                No achievements yet
              </h3>
              <p className="text-muted-foreground">
                Start reading devotionals to unlock your first achievement!
              </p>
            </div>
          )}
        </motion.div>
      </main>
    </div>
  );
};

export default Achievements;
