/**
 * Badge System 2.0 API
 * RESTful API endpoints for managing role-specific badges and volunteer achievements
 */

const express = require('express');
const { Pool } = require('pg');
const router = express.Router();

// Database connection (configure based on your setup)
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

/**
 * GET /api/badges/volunteers
 * Get all volunteers with their badge profiles
 */
router.get('/volunteers', async (req, res) => {
  try {
    const { page = 1, limit = 20, sortBy = 'badge_score', sortOrder = 'DESC' } = req.query;
    const offset = (page - 1) * limit;

    const query = `
      SELECT 
        vp.*,
        COUNT(vb.id) as total_badges,
        COUNT(CASE WHEN bd.rarity = 'legendary' THEN 1 END) as legendary_badges,
        COUNT(CASE WHEN bd.rarity = 'epic' THEN 1 END) as epic_badges,
        COUNT(CASE WHEN bd.rarity = 'rare' THEN 1 END) as rare_badges,
        vr.name as current_role_name
      FROM volunteer_profiles vp
      LEFT JOIN volunteer_badges vb ON vp.id = vb.volunteer_id
      LEFT JOIN badge_definitions bd ON vb.badge_id = bd.id
      LEFT JOIN volunteer_roles vr ON vp.current_role = vr.role_key
      GROUP BY vp.id, vr.name
      ORDER BY ${sortBy} ${sortOrder}
      LIMIT $1 OFFSET $2
    `;

    const result = await pool.query(query, [limit, offset]);
    
    // Get total count for pagination
    const countResult = await pool.query('SELECT COUNT(*) FROM volunteer_profiles');
    const totalCount = parseInt(countResult.rows[0].count);

    res.json({
      success: true,
      data: result.rows,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total: totalCount,
        totalPages: Math.ceil(totalCount / limit)
      }
    });
  } catch (error) {
    console.error('Error fetching volunteers:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

/**
 * GET /api/badges/volunteer/:id
 * Get detailed badge profile for a specific volunteer
 */
router.get('/volunteer/:id', async (req, res) => {
  try {
    const { id } = req.params;

    // Get volunteer profile
    const volunteerQuery = `
      SELECT vp.*, vr.name as current_role_name, vr.level as current_role_level
      FROM volunteer_profiles vp
      LEFT JOIN volunteer_roles vr ON vp.current_role = vr.role_key
      WHERE vp.id = $1
    `;
    const volunteerResult = await pool.query(volunteerQuery, [id]);
    
    if (volunteerResult.rows.length === 0) {
      return res.status(404).json({ success: false, error: 'Volunteer not found' });
    }

    const volunteer = volunteerResult.rows[0];

    // Get earned badges
    const badgesQuery = `
      SELECT bd.*, vb.earned_at, vb.earned_hours
      FROM volunteer_badges vb
      JOIN badge_definitions bd ON vb.badge_id = bd.id
      WHERE vb.volunteer_id = $1
      ORDER BY vb.earned_at DESC
    `;
    const badgesResult = await pool.query(badgesQuery, [id]);

    // Get storyworld participation
    const storyworldsQuery = `
      SELECT * FROM volunteer_storyworlds
      WHERE volunteer_id = $1 AND is_active = true
      ORDER BY hours_contributed DESC
    `;
    const storyworldsResult = await pool.query(storyworldsQuery, [id]);

    // Get training/certifications
    const trainingQuery = `
      SELECT * FROM volunteer_training
      WHERE volunteer_id = $1 AND is_current = true
      ORDER BY completed_at DESC
    `;
    const trainingResult = await pool.query(trainingQuery, [id]);

    // Get recent achievements
    const achievementsQuery = `
      SELECT * FROM achievement_history
      WHERE volunteer_id = $1
      ORDER BY achieved_at DESC
      LIMIT 10
    `;
    const achievementsResult = await pool.query(achievementsQuery, [id]);

    // Get recommendations
    const recommendationsQuery = `
      SELECT * FROM volunteer_recommendations
      WHERE volunteer_id = $1 AND is_completed = false
      ORDER BY priority DESC, created_at DESC
    `;
    const recommendationsResult = await pool.query(recommendationsQuery, [id]);

    res.json({
      success: true,
      data: {
        volunteer,
        badges: badgesResult.rows,
        storyworlds: storyworldsResult.rows,
        training: trainingResult.rows,
        achievements: achievementsResult.rows,
        recommendations: recommendationsResult.rows
      }
    });
  } catch (error) {
    console.error('Error fetching volunteer profile:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

/**
 * POST /api/badges/award
 * Award a badge to a volunteer
 */
router.post('/award', async (req, res) => {
  try {
    const { volunteerId, badgeKey, earnedHours, metadata = {} } = req.body;

    if (!volunteerId || !badgeKey) {
      return res.status(400).json({ 
        success: false, 
        error: 'volunteerId and badgeKey are required' 
      });
    }

    const client = await pool.connect();
    
    try {
      await client.query('BEGIN');

      // Get badge definition
      const badgeQuery = 'SELECT * FROM badge_definitions WHERE badge_key = $1';
      const badgeResult = await client.query(badgeQuery, [badgeKey]);
      
      if (badgeResult.rows.length === 0) {
        throw new Error(`Badge with key ${badgeKey} not found`);
      }

      const badge = badgeResult.rows[0];

      // Check if volunteer already has this badge
      const existingBadgeQuery = `
        SELECT id FROM volunteer_badges 
        WHERE volunteer_id = $1 AND badge_id = $2
      `;
      const existingResult = await client.query(existingBadgeQuery, [volunteerId, badge.id]);
      
      if (existingResult.rows.length > 0) {
        throw new Error('Volunteer already has this badge');
      }

      // Award the badge
      const awardQuery = `
        INSERT INTO volunteer_badges (volunteer_id, badge_id, earned_hours, metadata)
        VALUES ($1, $2, $3, $4)
        RETURNING *
      `;
      const awardResult = await client.query(awardQuery, [
        volunteerId, 
        badge.id, 
        earnedHours,
        JSON.stringify(metadata)
      ]);

      // Update volunteer badge score
      const updateScoreQuery = `
        UPDATE volunteer_profiles 
        SET badge_score = badge_score + $1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $2
      `;
      await client.query(updateScoreQuery, [badge.points, volunteerId]);

      // Record achievement in history
      const achievementQuery = `
        INSERT INTO achievement_history (volunteer_id, achievement_type, title, description, icon, metadata)
        VALUES ($1, 'badge_earned', $2, $3, $4, $5)
      `;
      await client.query(achievementQuery, [
        volunteerId,
        `Earned ${badge.name}!`,
        `Unlocked a ${badge.rarity} badge`,
        badge.icon,
        JSON.stringify({ badgeKey, rarity: badge.rarity })
      ]);

      await client.query('COMMIT');

      res.json({
        success: true,
        data: {
          award: awardResult.rows[0],
          badge
        },
        message: `Badge ${badge.name} awarded successfully!`
      });
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  } catch (error) {
    console.error('Error awarding badge:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

/**
 * POST /api/badges/calculate
 * Calculate and award eligible badges for a volunteer
 */
router.post('/calculate/:volunteerId', async (req, res) => {
  try {
    const { volunteerId } = req.params;
    const client = await pool.connect();
    
    try {
      await client.query('BEGIN');

      // Get volunteer profile with current data
      const volunteerQuery = `
        SELECT vp.*, 
               COUNT(vs.id) as storyworld_count,
               ARRAY_AGG(DISTINCT vs.storyworld_name) as storyworlds
        FROM volunteer_profiles vp
        LEFT JOIN volunteer_storyworlds vs ON vp.id = vs.volunteer_id AND vs.is_active = true
        WHERE vp.id = $1
        GROUP BY vp.id
      `;
      const volunteerResult = await client.query(volunteerQuery, [volunteerId]);
      
      if (volunteerResult.rows.length === 0) {
        return res.status(404).json({ success: false, error: 'Volunteer not found' });
      }

      const volunteer = volunteerResult.rows[0];

      // Get currently earned badges
      const earnedBadgesQuery = `
        SELECT bd.badge_key FROM volunteer_badges vb
        JOIN badge_definitions bd ON vb.badge_id = bd.id
        WHERE vb.volunteer_id = $1
      `;
      const earnedResult = await client.query(earnedBadgesQuery, [volunteerId]);
      const earnedBadgeKeys = earnedResult.rows.map(row => row.badge_key);

      // Get all available badge definitions
      const availableBadgesQuery = `
        SELECT * FROM badge_definitions 
        WHERE is_active = true 
        ORDER BY 
          CASE rarity 
            WHEN 'common' THEN 1
            WHEN 'uncommon' THEN 2  
            WHEN 'rare' THEN 3
            WHEN 'epic' THEN 4
            WHEN 'legendary' THEN 5
          END
      `;
      const availableResult = await client.query(availableBadgesQuery);
      
      const newBadges = [];
      
      for (const badge of availableResult.rows) {
        // Skip if already earned
        if (earnedBadgeKeys.includes(badge.badge_key)) continue;

        let eligible = false;

        // Check basic hour requirements
        if (volunteer.total_hours >= badge.required_hours) {
          if (badge.category === 'storyworld' && badge.storyworld) {
            // Check storyworld-specific badges
            if (volunteer.storyworlds && volunteer.storyworlds.includes(badge.storyworld)) {
              eligible = true;
            }
          } else if (badge.category === 'special') {
            // Check special badge requirements
            if (badge.badge_key === 'MULTI_TALENT' && volunteer.storyworld_count >= 3) {
              eligible = true;
            } else if (badge.badge_key === 'CONSISTENCY_CHAMPION' && volunteer.years_active >= 1) {
              eligible = true;
            }
          } else if (badge.category === 'role') {
            // Role badges would be awarded through role progression system
            eligible = false;
          } else {
            // General badges
            eligible = true;
          }
        }

        // Check years requirement
        if (eligible && badge.required_years > volunteer.years_active) {
          eligible = false;
        }

        // Check storyworld count requirement (for multi-talent type badges)
        if (eligible && badge.required_categories > volunteer.storyworld_count) {
          eligible = false;
        }

        if (eligible) {
          // Award the badge
          const awardQuery = `
            INSERT INTO volunteer_badges (volunteer_id, badge_id, earned_hours)
            VALUES ($1, $2, $3)
            RETURNING *
          `;
          const awardResult = await client.query(awardQuery, [
            volunteerId, 
            badge.id, 
            volunteer.total_hours
          ]);

          // Update badge score
          const updateScoreQuery = `
            UPDATE volunteer_profiles 
            SET badge_score = badge_score + $1
            WHERE id = $2
          `;
          await client.query(updateScoreQuery, [badge.points, volunteerId]);

          // Record achievement
          const achievementQuery = `
            INSERT INTO achievement_history (volunteer_id, achievement_type, title, description, icon, metadata)
            VALUES ($1, 'badge_earned', $2, $3, $4, $5)
          `;
          await client.query(achievementQuery, [
            volunteerId,
            `Earned ${badge.name}!`,
            `Unlocked a ${badge.rarity} badge`,
            badge.icon,
            JSON.stringify({ badgeKey: badge.badge_key, rarity: badge.rarity })
          ]);

          newBadges.push({
            award: awardResult.rows[0],
            badge
          });
        }
      }

      await client.query('COMMIT');

      res.json({
        success: true,
        data: {
          newBadges,
          totalAwarded: newBadges.length
        },
        message: `${newBadges.length} new badges awarded!`
      });
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  } catch (error) {
    console.error('Error calculating badges:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

/**
 * GET /api/badges/leaderboard
 * Get badge leaderboard
 */
router.get('/leaderboard', async (req, res) => {
  try {
    const { limit = 20 } = req.query;

    const query = `
      SELECT 
        vp.id,
        vp.first_name,
        vp.last_name,
        vp.badge_score,
        vp.total_hours,
        COUNT(vb.id) as total_badges,
        COUNT(CASE WHEN bd.rarity = 'legendary' THEN 1 END) as legendary_badges,
        COUNT(CASE WHEN bd.rarity = 'epic' THEN 1 END) as epic_badges,
        vr.name as current_role_name,
        vr.level as current_role_level
      FROM volunteer_profiles vp
      LEFT JOIN volunteer_badges vb ON vp.id = vb.volunteer_id
      LEFT JOIN badge_definitions bd ON vb.badge_id = bd.id
      LEFT JOIN volunteer_roles vr ON vp.current_role = vr.role_key
      GROUP BY vp.id, vr.name, vr.level
      ORDER BY vp.badge_score DESC, vp.total_hours DESC
      LIMIT $1
    `;

    const result = await pool.query(query, [limit]);

    res.json({
      success: true,
      data: result.rows
    });
  } catch (error) {
    console.error('Error fetching leaderboard:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

/**
 * GET /api/badges/statistics
 * Get badge system statistics
 */
router.get('/statistics', async (req, res) => {
  try {
    // Total badges awarded
    const totalBadgesQuery = 'SELECT COUNT(*) as total FROM volunteer_badges';
    const totalBadgesResult = await pool.query(totalBadgesQuery);

    // Badges by rarity
    const rarityQuery = `
      SELECT bd.rarity, COUNT(vb.id) as count
      FROM badge_definitions bd
      LEFT JOIN volunteer_badges vb ON bd.id = vb.badge_id
      GROUP BY bd.rarity
      ORDER BY 
        CASE bd.rarity 
          WHEN 'common' THEN 1
          WHEN 'uncommon' THEN 2  
          WHEN 'rare' THEN 3
          WHEN 'epic' THEN 4
          WHEN 'legendary' THEN 5
        END
    `;
    const rarityResult = await pool.query(rarityQuery);

    // Badges by category
    const categoryQuery = `
      SELECT bd.category, COUNT(vb.id) as count
      FROM badge_definitions bd
      LEFT JOIN volunteer_badges vb ON bd.id = vb.badge_id
      GROUP BY bd.category
    `;
    const categoryResult = await pool.query(categoryQuery);

    // Role distribution
    const roleQuery = `
      SELECT vr.name, vr.level, COUNT(vp.id) as count
      FROM volunteer_roles vr
      LEFT JOIN volunteer_profiles vp ON vr.role_key = vp.current_role
      GROUP BY vr.name, vr.level
      ORDER BY vr.level
    `;
    const roleResult = await pool.query(roleQuery);

    // Average badge score
    const avgScoreQuery = 'SELECT AVG(badge_score) as avg_score FROM volunteer_profiles';
    const avgScoreResult = await pool.query(avgScoreQuery);

    res.json({
      success: true,
      data: {
        totalBadges: parseInt(totalBadgesResult.rows[0].total),
        badgesByRarity: rarityResult.rows.reduce((acc, row) => {
          acc[row.rarity] = parseInt(row.count);
          return acc;
        }, {}),
        badgesByCategory: categoryResult.rows.reduce((acc, row) => {
          acc[row.category] = parseInt(row.count);
          return acc;
        }, {}),
        roleDistribution: roleResult.rows,
        averageBadgeScore: Math.round(parseFloat(avgScoreResult.rows[0].avg_score) || 0)
      }
    });
  } catch (error) {
    console.error('Error fetching statistics:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

/**
 * PUT /api/badges/volunteer/:id/role
 * Update volunteer role
 */
router.put('/volunteer/:id/role', async (req, res) => {
  try {
    const { id } = req.params;
    const { roleKey } = req.body;

    if (!roleKey) {
      return res.status(400).json({ success: false, error: 'roleKey is required' });
    }

    const client = await pool.connect();
    
    try {
      await client.query('BEGIN');

      // Validate role exists
      const roleQuery = 'SELECT * FROM volunteer_roles WHERE role_key = $1';
      const roleResult = await client.query(roleQuery, [roleKey]);
      
      if (roleResult.rows.length === 0) {
        throw new Error(`Role ${roleKey} not found`);
      }

      const role = roleResult.rows[0];

      // Update volunteer role
      const updateQuery = `
        UPDATE volunteer_profiles 
        SET current_role = $1, updated_at = CURRENT_TIMESTAMP
        WHERE id = $2
        RETURNING *
      `;
      const updateResult = await client.query(updateQuery, [roleKey, id]);

      // Record role change in achievement history
      const achievementQuery = `
        INSERT INTO achievement_history (volunteer_id, achievement_type, title, description, icon)
        VALUES ($1, 'role_change', $2, $3, '🎖️')
      `;
      await client.query(achievementQuery, [
        id,
        `Promoted to ${role.name}!`,
        `Advanced to level ${role.level} role`
      ]);

      await client.query('COMMIT');

      res.json({
        success: true,
        data: updateResult.rows[0],
        message: `Role updated to ${role.name}`
      });
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  } catch (error) {
    console.error('Error updating volunteer role:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;