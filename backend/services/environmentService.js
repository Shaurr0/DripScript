/**
 * Environment Service - Main service that coordinates weather and air quality data
 * Prepares comprehensive environmental data for AI outfit recommendations
 */

import WeatherService from './weatherService.js';
import AirQualityService from './airQualityService.js';

class EnvironmentService {
  constructor(config) {
    this.weatherService = new WeatherService(config.openWeatherApiKey);
    this.airQualityService = new AirQualityService(
      config.aqicnToken, 
      config.openWeatherApiKey
    );
    this.defaultLocation = config.defaultLocation || { lat: 40.7128, lon: -74.0060 }; // NYC default
  }

  /**
   * Get user's current location using browser geolocation API
   * @returns {Promise<Object>} Location coordinates
   */
  async getCurrentLocation() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation is not supported by this browser'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            lat: position.coords.latitude,
            lon: position.coords.longitude,
            accuracy: position.coords.accuracy
          });
        },
        (error) => {
          console.warn('Geolocation failed:', error.message);
          // Fallback to default location
          resolve(this.defaultLocation);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 300000 // 5 minutes
        }
      );
    });
  }

  /**
   * Get comprehensive environmental data for AI processing
   * @param {Object} location - Optional location override {lat, lon}
   * @returns {Promise<Object>} Complete environmental data package
   */
  async getEnvironmentalData(location = null) {
    try {
      // Get location
      const coords = location || await this.getCurrentLocation();
      
      // Fetch weather and air quality data in parallel
      const [weatherData, airQualityData] = await Promise.all([
        this.weatherService.getCurrentWeather(coords.lat, coords.lon),
        this.airQualityService.getAirQualityData(coords.lat, coords.lon)
      ]);

      // Get additional weather insights
      const [forecast, rainPrediction] = await Promise.all([
        this.weatherService.getWeatherForecast(coords.lat, coords.lon),
        this.weatherService.getRainForecast(coords.lat, coords.lon)
      ]);

      // Prepare comprehensive data for AI layer
      const environmentalContext = {
        timestamp: new Date().toISOString(),
        location: {
          latitude: coords.lat,
          longitude: coords.lon,
          city: weatherData.location
        },
        weather: {
          current: {
            temperature: weatherData.temperature,
            feelsLike: weatherData.feelsLike,
            humidity: weatherData.humidity,
            description: weatherData.description,
            main: weatherData.main,
            windSpeed: weatherData.windSpeed,
            pressure: weatherData.pressure
          },
          forecast: forecast.forecasts.slice(0, 2), // Today and tomorrow
          rain: {
            probability: rainPrediction.probability,
            expected: rainPrediction.willRain,
            recommendation: rainPrediction.recommendation
          }
        },
        airQuality: {
          aqi: airQualityData.aqi,
          level: airQualityData.level,
          description: airQualityData.description,
          dominentPollutant: airQualityData.dominentPollutant,
          healthImpact: airQualityData.healthRecommendation,
          clothingImpact: airQualityData.clothingImpact,
          source: airQualityData.source
        },
        recommendations: this.generateEnvironmentalRecommendations(weatherData, airQualityData, rainPrediction)
      };

      return environmentalContext;
    } catch (error) {
      console.error('Error getting environmental data:', error);
      throw error;
    }
  }

  /**
   * Generate clothing recommendations based on environmental factors
   * @param {Object} weatherData - Current weather data
   * @param {Object} airQualityData - Air quality data
   * @param {Object} rainData - Rain prediction data
   * @returns {Object} Environmental recommendations for outfit selection
   */
  generateEnvironmentalRecommendations(weatherData, airQualityData, rainData) {
    const recommendations = {
      temperature: this.getTemperatureRecommendations(weatherData.temperature, weatherData.feelsLike),
      weather: this.getWeatherRecommendations(weatherData.main, weatherData.windSpeed),
      rain: this.getRainRecommendations(rainData),
      airQuality: airQualityData.clothingImpact,
      overall: []
    };

    // Generate overall recommendations
    const overall = [];

    // Temperature-based recommendations
    if (weatherData.temperature < 10) {
      overall.push('Wear warm, layered clothing');
    } else if (weatherData.temperature > 25) {
      overall.push('Choose light, breathable fabrics');
    }

    // Weather-based recommendations
    if (weatherData.main === 'Rain' || rainData.willRain) {
      overall.push('Bring waterproof clothing or umbrella');
    }

    if (weatherData.windSpeed > 5) {
      overall.push('Consider wind-resistant outerwear');
    }

    // Air quality recommendations
    if (airQualityData.aqi > 100) {
      overall.push('Wear mask and minimize skin exposure');
    }

    // Humidity recommendations
    if (weatherData.humidity > 70) {
      overall.push('Choose moisture-wicking fabrics');
    }

    recommendations.overall = overall;
    return recommendations;
  }

  /**
   * Get temperature-specific clothing recommendations
   * @param {number} temp - Current temperature
   * @param {number} feelsLike - Feels-like temperature
   * @returns {Object} Temperature recommendations
   */
  getTemperatureRecommendations(temp, feelsLike) {
    const effectiveTemp = feelsLike || temp;
    
    if (effectiveTemp < 0) {
      return {
        category: 'freezing',
        clothing: ['heavy_coat', 'thermal_layers', 'warm_accessories'],
        fabrics: ['wool', 'down', 'fleece'],
        message: 'Bundle up! Heavy winter clothing needed'
      };
    } else if (effectiveTemp < 10) {
      return {
        category: 'cold',
        clothing: ['coat', 'long_sleeves', 'closed_shoes'],
        fabrics: ['wool', 'cotton', 'synthetic_blends'],
        message: 'Cool weather - layers recommended'
      };
    } else if (effectiveTemp < 20) {
      return {
        category: 'mild',
        clothing: ['light_jacket', 'long_or_short_sleeves'],
        fabrics: ['cotton', 'light_wool'],
        message: 'Mild weather - light layers work well'
      };
    } else if (effectiveTemp < 30) {
      return {
        category: 'warm',
        clothing: ['short_sleeves', 'light_pants', 'breathable_shoes'],
        fabrics: ['cotton', 'linen', 'moisture_wicking'],
        message: 'Warm weather - light, breathable clothing'
      };
    } else {
      return {
        category: 'hot',
        clothing: ['minimal_coverage', 'shorts', 'sandals'],
        fabrics: ['linen', 'cotton', 'moisture_wicking'],
        message: 'Hot weather - stay cool and protected'
      };
    }
  }

  /**
   * Get weather condition specific recommendations
   * @param {string} condition - Weather condition
   * @param {number} windSpeed - Wind speed
   * @returns {Object} Weather recommendations
   */
  getWeatherRecommendations(condition, windSpeed) {
    const recommendations = {
      condition: condition.toLowerCase(),
      accessories: [],
      protection: []
    };

    switch (condition.toLowerCase()) {
      case 'rain':
      case 'drizzle':
        recommendations.accessories.push('umbrella', 'waterproof_jacket');
        recommendations.protection.push('water_resistance');
        break;
      case 'snow':
        recommendations.accessories.push('warm_hat', 'gloves', 'waterproof_boots');
        recommendations.protection.push('insulation', 'water_resistance');
        break;
      case 'clear':
      case 'sunny':
        recommendations.accessories.push('sunglasses', 'hat');
        recommendations.protection.push('uv_protection');
        break;
      case 'clouds':
        recommendations.accessories.push('light_jacket');
        break;
    }

    if (windSpeed > 5) {
      recommendations.accessories.push('wind_resistant_outer_layer');
      recommendations.protection.push('wind_resistance');
    }

    return recommendations;
  }

  /**
   * Get rain-specific recommendations
   * @param {Object} rainData - Rain prediction data
   * @returns {Object} Rain recommendations
   */
  getRainRecommendations(rainData) {
    return {
      expected: rainData.willRain,
      probability: rainData.probability,
      items: rainData.willRain ? ['umbrella', 'waterproof_jacket', 'closed_shoes'] : [],
      message: rainData.probability > 50 ? 'High chance of rain - be prepared' : 
               rainData.probability > 30 ? 'Possible rain - consider light rain gear' : 
               'Low chance of rain'
    };
  }

  /**
   * Get formatted display data for UI context bar
   * @param {Object} location - Optional location override
   * @returns {Promise<Object>} Formatted display data
   */
  async getDisplayData(location = null) {
    try {
      const envData = await this.getEnvironmentalData(location);
      
      return {
        weather: `${envData.weather.current.temperature}°C`,
        aqi: envData.airQuality.aqi || 'N/A',
        condition: envData.weather.current.description,
        location: envData.location.city,
        timestamp: new Date().toLocaleTimeString(),
        alerts: this.generateAlerts(envData)
      };
    } catch (error) {
      console.error('Error getting display data:', error);
      return {
        weather: 'N/A',
        aqi: 'N/A',
        condition: 'Data unavailable',
        location: 'Unknown',
        timestamp: new Date().toLocaleTimeString(),
        alerts: ['Unable to fetch environmental data']
      };
    }
  }

  /**
   * Generate alerts based on environmental conditions
   * @param {Object} envData - Environmental data
   * @returns {Array} Array of alert messages
   */
  generateAlerts(envData) {
    const alerts = [];
    
    // Temperature alerts
    if (envData.weather.current.temperature < 0) {
      alerts.push('⚠️ Freezing temperatures - dress warmly');
    } else if (envData.weather.current.temperature > 35) {
      alerts.push('🌡️ Very hot - stay hydrated and cool');
    }

    // Rain alerts
    if (envData.weather.rain.probability > 70) {
      alerts.push('🌧️ High chance of rain - bring umbrella');
    }

    // Air quality alerts
    if (envData.airQuality.aqi > 150) {
      alerts.push('😷 Poor air quality - consider wearing mask');
    }

    // Wind alerts
    if (envData.weather.current.windSpeed > 10) {
      alerts.push('💨 Windy conditions - secure loose clothing');
    }

    return alerts;
  }
}

export default EnvironmentService;