/**
 * Environment Data Processor - Formats environmental data for AI outfit recommendations
 * Converts complex environmental data into structured JSON for the AI layer
 */

class EnvironmentDataProcessor {
  /**
   * Process environmental data for AI consumption
   * @param {Object} environmentalData - Raw environmental data from EnvironmentService
   * @returns {Object} Processed data optimized for AI outfit recommendations
   */
  static processForAI(environmentalData) {
    const processedData = {
      metadata: {
        timestamp: environmentalData.timestamp,
        location: environmentalData.location,
        dataVersion: '1.0'
      },
      environmental_factors: {
        temperature: this.processTemperatureData(environmentalData.weather),
        precipitation: this.processPrecipitationData(environmentalData.weather),
        air_quality: this.processAirQualityData(environmentalData.airQuality),
        wind: this.processWindData(environmentalData.weather),
        humidity: this.processHumidityData(environmentalData.weather),
        uv_conditions: this.processUVData(environmentalData.weather)
      },
      comfort_factors: {
        thermal_comfort: this.calculateThermalComfort(environmentalData.weather),
        outdoor_suitability: this.assessOutdoorSuitability(environmentalData),
        health_considerations: this.extractHealthConsiderations(environmentalData)
      },
      outfit_constraints: this.generateOutfitConstraints(environmentalData),
      recommendations: this.formatRecommendationsForAI(environmentalData.recommendations),
      risk_factors: this.identifyRiskFactors(environmentalData)
    };

    return processedData;
  }

  /**
   * Process temperature data for AI analysis
   * @param {Object} weatherData - Weather data object
   * @returns {Object} Processed temperature information
   */
  static processTemperatureData(weatherData) {
    const current = weatherData.current;
    const forecast = weatherData.forecast[0] || {};
    
    return {
      current_celsius: current.temperature,
      feels_like_celsius: current.feelsLike,
      comfort_category: this.categorizeTemperature(current.feelsLike || current.temperature),
      daily_range: {
        min: forecast.minTemp || current.temperature - 3,
        max: forecast.maxTemp || current.temperature + 3
      },
      layering_need: this.assessLayeringNeed(current.temperature, current.feelsLike),
      fabric_recommendations: this.getFabricRecommendations(current.temperature)
    };
  }

  /**
   * Process precipitation data
   * @param {Object} weatherData - Weather data object
   * @returns {Object} Processed precipitation information
   */
  static processPrecipitationData(weatherData) {
    const rain = weatherData.rain;
    
    return {
      probability_percent: rain.probability,
      expected: rain.expected,
      intensity: this.classifyRainIntensity(rain.probability),
      protection_needed: rain.probability > 30,
      recommended_gear: rain.expected ? ['umbrella', 'waterproof_jacket'] : [],
      impact_on_outfit: this.assessRainImpact(rain.probability)
    };
  }

  /**
   * Process air quality data
   * @param {Object} airQualityData - Air quality data object
   * @returns {Object} Processed air quality information
   */
  static processAirQualityData(airQualityData) {
    return {
      aqi_value: airQualityData.aqi,
      quality_level: airQualityData.level,
      health_impact: airQualityData.healthImpact?.general || 'Unknown',
      mask_recommended: airQualityData.clothingImpact?.mask || false,
      skin_protection: airQualityData.clothingImpact?.coverage || 'normal',
      outdoor_activity_advice: this.getActivityAdvice(airQualityData.aqi),
      dominant_pollutant: airQualityData.dominentPollutant
    };
  }

  /**
   * Process wind data
   * @param {Object} weatherData - Weather data object
   * @returns {Object} Processed wind information
   */
  static processWindData(weatherData) {
    const windSpeed = weatherData.current.windSpeed;
    
    return {
      speed_ms: windSpeed,
      strength_category: this.categorizeWindStrength(windSpeed),
      clothing_impact: windSpeed > 5 ? 'high' : windSpeed > 2 ? 'medium' : 'low',
      recommended_adjustments: this.getWindAdjustments(windSpeed)
    };
  }

  /**
   * Process humidity data
   * @param {Object} weatherData - Weather data object
   * @returns {Object} Processed humidity information
   */
  static processHumidityData(weatherData) {
    const humidity = weatherData.current.humidity;
    
    return {
      relative_humidity_percent: humidity,
      comfort_level: this.categorizeHumidity(humidity),
      fabric_preference: this.getHumidityFabricPreference(humidity),
      breathability_importance: humidity > 60 ? 'high' : 'medium'
    };
  }

  /**
   * Process UV conditions (estimated based on weather conditions)
   * @param {Object} weatherData - Weather data object
   * @returns {Object} Processed UV information
   */
  static processUVData(weatherData) {
    const condition = weatherData.current.main.toLowerCase();
    const estimatedUVIndex = this.estimateUVIndex(condition);
    
    return {
      estimated_uv_index: estimatedUVIndex,
      protection_needed: estimatedUVIndex > 3,
      recommended_protection: estimatedUVIndex > 6 ? ['hat', 'sunglasses', 'long_sleeves'] : 
                              estimatedUVIndex > 3 ? ['sunglasses'] : [],
      skin_exposure_advice: estimatedUVIndex > 7 ? 'minimize' : 'moderate'
    };
  }

  /**
   * Calculate thermal comfort index
   * @param {Object} weatherData - Weather data object
   * @returns {Object} Thermal comfort assessment
   */
  static calculateThermalComfort(weatherData) {
    const temp = weatherData.current.temperature;
    const humidity = weatherData.current.humidity;
    const wind = weatherData.current.windSpeed;
    
    // Simplified heat index calculation
    let comfortIndex = temp;
    if (humidity > 40) {
      comfortIndex += (humidity - 40) * 0.1; // Increase perceived temperature with humidity
    }
    if (wind > 2) {
      comfortIndex -= Math.min(wind * 0.5, 3); // Wind chill effect
    }
    
    return {
      comfort_index: Math.round(comfortIndex),
      comfort_level: this.getComfortLevel(comfortIndex),
      adjustment_needed: Math.abs(comfortIndex - 22) > 3 // Ideal comfort around 22°C
    };
  }

  /**
   * Assess outdoor activity suitability
   * @param {Object} environmentalData - Complete environmental data
   * @returns {Object} Outdoor suitability assessment
   */
  static assessOutdoorSuitability(environmentalData) {
    const weather = environmentalData.weather;
    const airQuality = environmentalData.airQuality;
    
    let score = 10; // Start with perfect score
    
    // Temperature penalties
    if (weather.current.temperature < 0 || weather.current.temperature > 35) score -= 3;
    else if (weather.current.temperature < 5 || weather.current.temperature > 30) score -= 1;
    
    // Rain penalties
    if (weather.rain.probability > 70) score -= 3;
    else if (weather.rain.probability > 40) score -= 1;
    
    // Air quality penalties
    if (airQuality.aqi > 150) score -= 3;
    else if (airQuality.aqi > 100) score -= 1;
    
    // Wind penalties
    if (weather.current.windSpeed > 10) score -= 2;
    else if (weather.current.windSpeed > 6) score -= 1;
    
    return {
      suitability_score: Math.max(0, score),
      suitability_level: score > 7 ? 'excellent' : score > 5 ? 'good' : score > 3 ? 'fair' : 'poor',
      limiting_factors: this.identifyLimitingFactors(environmentalData)
    };
  }

  /**
   * Extract health considerations
   * @param {Object} environmentalData - Environmental data
   * @returns {Object} Health considerations
   */
  static extractHealthConsiderations(environmentalData) {
    return {
      air_quality_concerns: environmentalData.airQuality.healthImpact,
      temperature_risks: this.getTemperatureRisks(environmentalData.weather.current.temperature),
      special_populations: this.getSpecialPopulationAdvice(environmentalData),
      protective_measures: this.getProtectiveMeasures(environmentalData)
    };
  }

  /**
   * Generate outfit constraints based on environmental conditions
   * @param {Object} environmentalData - Environmental data
   * @returns {Object} Outfit constraints
   */
  static generateOutfitConstraints(environmentalData) {
    return {
      must_have: this.getMustHaveItems(environmentalData),
      avoid: this.getItemsToAvoid(environmentalData),
      material_preferences: this.getMaterialPreferences(environmentalData),
      coverage_requirements: this.getCoverageRequirements(environmentalData),
      special_features: this.getSpecialFeatures(environmentalData)
    };
  }

  /**
   * Format recommendations for AI processing
   * @param {Object} recommendations - Original recommendations
   * @returns {Object} AI-formatted recommendations
   */
  static formatRecommendationsForAI(recommendations) {
    return {
      priority_items: recommendations.overall.slice(0, 3),
      temperature_guidance: recommendations.temperature.message,
      weather_adaptations: recommendations.weather.accessories || [],
      protective_gear: recommendations.rain.items || [],
      comfort_enhancements: this.getComfortEnhancements(recommendations)
    };
  }

  /**
   * Identify risk factors that affect outfit choices
   * @param {Object} environmentalData - Environmental data
   * @returns {Array} Array of risk factors
   */
  static identifyRiskFactors(environmentalData) {
    const risks = [];
    
    if (environmentalData.weather.current.temperature < -5) {
      risks.push({ type: 'frostbite', severity: 'high', recommendation: 'Full body coverage required' });
    }
    
    if (environmentalData.weather.current.temperature > 40) {
      risks.push({ type: 'heat_exhaustion', severity: 'high', recommendation: 'Minimal, breathable clothing' });
    }
    
    if (environmentalData.weather.rain.probability > 80) {
      risks.push({ type: 'water_exposure', severity: 'medium', recommendation: 'Waterproof clothing essential' });
    }
    
    if (environmentalData.airQuality.aqi > 200) {
      risks.push({ type: 'air_pollution', severity: 'high', recommendation: 'Minimize skin exposure, wear mask' });
    }
    
    if (environmentalData.weather.current.windSpeed > 15) {
      risks.push({ type: 'wind_exposure', severity: 'medium', recommendation: 'Secure, wind-resistant clothing' });
    }
    
    return risks;
  }

  // Helper methods for categorization and assessment

  static categorizeTemperature(temp) {
    if (temp < 0) return 'freezing';
    if (temp < 10) return 'cold';
    if (temp < 20) return 'cool';
    if (temp < 25) return 'comfortable';
    if (temp < 30) return 'warm';
    return 'hot';
  }

  static categorizeWindStrength(speed) {
    if (speed < 2) return 'calm';
    if (speed < 6) return 'light';
    if (speed < 12) return 'moderate';
    if (speed < 20) return 'strong';
    return 'very_strong';
  }

  static categorizeHumidity(humidity) {
    if (humidity < 30) return 'dry';
    if (humidity < 60) return 'comfortable';
    if (humidity < 80) return 'humid';
    return 'very_humid';
  }

  static estimateUVIndex(condition) {
    switch (condition) {
      case 'clear':
      case 'sunny': return 8;
      case 'clouds': return 5;
      case 'rain':
      case 'drizzle': return 2;
      case 'snow': return 3;
      default: return 4;
    }
  }

  static getComfortLevel(index) {
    if (index < 16) return 'too_cold';
    if (index < 20) return 'cool';
    if (index < 26) return 'comfortable';
    if (index < 30) return 'warm';
    return 'too_hot';
  }

  static getMustHaveItems(envData) {
    const items = [];
    if (envData.weather.rain.expected) items.push('waterproof_jacket');
    if (envData.weather.current.temperature < 10) items.push('warm_layers');
    if (envData.airQuality.clothingImpact?.mask) items.push('face_mask');
    if (envData.weather.current.main.toLowerCase().includes('sun')) items.push('sun_protection');
    return items;
  }

  static getItemsToAvoid(envData) {
    const avoid = [];
    if (envData.weather.current.temperature > 30) avoid.push('heavy_fabrics', 'dark_colors');
    if (envData.weather.rain.probability > 50) avoid.push('suede', 'delicate_fabrics');
    if (envData.airQuality.aqi > 100) avoid.push('mesh_fabrics', 'cropped_tops');
    return avoid;
  }

  static getMaterialPreferences(envData) {
    const prefs = { preferred: [], avoid: [] };
    
    if (envData.weather.current.temperature > 25) {
      prefs.preferred.push('cotton', 'linen', 'moisture_wicking');
    } else if (envData.weather.current.temperature < 10) {
      prefs.preferred.push('wool', 'fleece', 'down');
    }
    
    if (envData.weather.current.humidity > 70) {
      prefs.preferred.push('breathable_synthetics');
      prefs.avoid.push('non_breathable_plastics');
    }
    
    return prefs;
  }

  static getCoverageRequirements(envData) {
    if (envData.airQuality.aqi > 150) return 'full_coverage';
    if (envData.weather.current.temperature < 5) return 'full_coverage';
    if (envData.weather.current.temperature > 30) return 'minimal_coverage';
    return 'moderate_coverage';
  }

  static getSpecialFeatures(envData) {
    const features = [];
    if (envData.weather.rain.expected) features.push('water_resistant');
    if (envData.weather.current.windSpeed > 8) features.push('wind_resistant');
    if (envData.weather.current.humidity > 70) features.push('moisture_wicking');
    if (envData.weather.current.temperature < 0) features.push('insulated');
    return features;
  }

  // Additional helper methods...
  static assessLayeringNeed(temp, feelsLike) {
    const effectiveTemp = feelsLike || temp;
    if (effectiveTemp < 0) return 'heavy_layering';
    if (effectiveTemp < 15) return 'moderate_layering';
    if (effectiveTemp < 25) return 'light_layering';
    return 'minimal_layering';
  }

  static getFabricRecommendations(temp) {
    if (temp < 0) return ['wool', 'down', 'fleece', 'thermal'];
    if (temp < 15) return ['wool', 'cotton', 'synthetic_blends'];
    if (temp < 25) return ['cotton', 'light_wool', 'blends'];
    return ['cotton', 'linen', 'moisture_wicking', 'bamboo'];
  }

  static classifyRainIntensity(probability) {
    if (probability < 20) return 'none';
    if (probability < 50) return 'light';
    if (probability < 80) return 'moderate';
    return 'heavy';
  }

  static assessRainImpact(probability) {
    if (probability < 30) return 'minimal';
    if (probability < 60) return 'moderate';
    return 'significant';
  }

  static getActivityAdvice(aqi) {
    if (aqi <= 50) return 'all_activities_safe';
    if (aqi <= 100) return 'normal_activities_ok';
    if (aqi <= 150) return 'limit_prolonged_outdoor';
    return 'avoid_outdoor_activities';
  }

  static getWindAdjustments(windSpeed) {
    if (windSpeed > 10) return ['secure_clothing', 'wind_resistant_outer_layer'];
    if (windSpeed > 5) return ['avoid_loose_items'];
    return [];
  }

  static getHumidityFabricPreference(humidity) {
    if (humidity > 70) return 'moisture_wicking_essential';
    if (humidity > 50) return 'breathable_preferred';
    return 'standard_ok';
  }

  static identifyLimitingFactors(envData) {
    const factors = [];
    if (envData.weather.current.temperature < 0) factors.push('extreme_cold');
    if (envData.weather.current.temperature > 35) factors.push('extreme_heat');
    if (envData.weather.rain.probability > 70) factors.push('heavy_rain_expected');
    if (envData.airQuality.aqi > 150) factors.push('poor_air_quality');
    if (envData.weather.current.windSpeed > 12) factors.push('strong_winds');
    return factors;
  }

  static getTemperatureRisks(temp) {
    if (temp < -10) return ['frostbite_risk', 'hypothermia_risk'];
    if (temp < 0) return ['cold_exposure_risk'];
    if (temp > 40) return ['heat_exhaustion_risk', 'dehydration_risk'];
    if (temp > 35) return ['overheating_risk'];
    return [];
  }

  static getSpecialPopulationAdvice(envData) {
    const advice = {};
    if (envData.airQuality.aqi > 100) {
      advice.sensitive_individuals = 'Extra protection recommended';
    }
    if (envData.weather.current.temperature < 5 || envData.weather.current.temperature > 30) {
      advice.elderly_children = 'Additional clothing layers recommended';
    }
    return advice;
  }

  static getProtectiveMeasures(envData) {
    const measures = [];
    if (envData.airQuality.aqi > 100) measures.push('wear_mask');
    if (envData.weather.current.temperature < 0) measures.push('protect_extremities');
    if (envData.weather.current.temperature > 35) measures.push('avoid_overheating');
    if (envData.weather.rain.expected) measures.push('waterproof_protection');
    return measures;
  }

  static getComfortEnhancements(recommendations) {
    const enhancements = [];
    if (recommendations.temperature?.category === 'hot') {
      enhancements.push('cooling_fabrics', 'loose_fit');
    }
    if (recommendations.temperature?.category === 'cold') {
      enhancements.push('insulation', 'wind_protection');
    }
    return enhancements;
  }
}

export default EnvironmentDataProcessor;