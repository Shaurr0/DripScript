/**
 * Weather Service - Integrates with OpenWeatherMap API
 * Handles temperature, humidity, and rain forecast data
 */

class WeatherService {
  constructor(apiKey) {
    this.apiKey = apiKey;
    this.baseUrl = 'https://api.openweathermap.org/data/2.5';
  }

  /**
   * Get current weather data for a location
   * @param {number} lat - Latitude
   * @param {number} lon - Longitude
   * @returns {Promise<Object>} Weather data
   */
  async getCurrentWeather(lat, lon) {
    try {
      const response = await fetch(
        `${this.baseUrl}/weather?lat=${lat}&lon=${lon}&appid=${this.apiKey}&units=metric`
      );
      
      if (!response.ok) {
        throw new Error(`Weather API error: ${response.status}`);
      }
      
      const data = await response.json();
      
      return {
        temperature: Math.round(data.main.temp),
        humidity: data.main.humidity,
        description: data.weather[0].description,
        main: data.weather[0].main,
        windSpeed: data.wind?.speed || 0,
        pressure: data.main.pressure,
        feelsLike: Math.round(data.main.feels_like),
        location: data.name
      };
    } catch (error) {
      console.error('Error fetching weather data:', error);
      throw error;
    }
  }

  /**
   * Get weather forecast for the next 5 days
   * @param {number} lat - Latitude
   * @param {number} lon - Longitude
   * @returns {Promise<Object>} Forecast data
   */
  async getWeatherForecast(lat, lon) {
    try {
      const response = await fetch(
        `${this.baseUrl}/forecast?lat=${lat}&lon=${lon}&appid=${this.apiKey}&units=metric`
      );
      
      if (!response.ok) {
        throw new Error(`Forecast API error: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Process forecast data - get daily summaries
      const dailyForecasts = this.processForecastData(data.list);
      
      return {
        location: data.city.name,
        forecasts: dailyForecasts
      };
    } catch (error) {
      console.error('Error fetching forecast data:', error);
      throw error;
    }
  }

  /**
   * Process raw forecast data into daily summaries
   * @param {Array} forecastList - Raw forecast data from API
   * @returns {Array} Processed daily forecasts
   */
  processForecastData(forecastList) {
    const dailyData = {};
    
    forecastList.forEach(item => {
      const date = new Date(item.dt * 1000).toDateString();
      
      if (!dailyData[date]) {
        dailyData[date] = {
          date,
          temperatures: [],
          humidity: [],
          rainProbability: 0,
          weather: item.weather[0].main,
          description: item.weather[0].description
        };
      }
      
      dailyData[date].temperatures.push(item.main.temp);
      dailyData[date].humidity.push(item.main.humidity);
      
      // Check for rain probability
      if (item.pop) {
        dailyData[date].rainProbability = Math.max(
          dailyData[date].rainProbability, 
          item.pop * 100
        );
      }
    });
    
    // Calculate averages and return formatted data
    return Object.values(dailyData).slice(0, 5).map(day => ({
      date: day.date,
      minTemp: Math.round(Math.min(...day.temperatures)),
      maxTemp: Math.round(Math.max(...day.temperatures)),
      avgHumidity: Math.round(day.humidity.reduce((a, b) => a + b, 0) / day.humidity.length),
      rainProbability: Math.round(day.rainProbability),
      weather: day.weather,
      description: day.description
    }));
  }

  /**
   * Check if it's likely to rain today
   * @param {number} lat - Latitude
   * @param {number} lon - Longitude
   * @returns {Promise<Object>} Rain prediction
   */
  async getRainForecast(lat, lon) {
    try {
      const forecast = await this.getWeatherForecast(lat, lon);
      const today = forecast.forecasts[0];
      
      return {
        willRain: today.rainProbability > 30,
        probability: today.rainProbability,
        recommendation: today.rainProbability > 50 ? 'umbrella' : 'light_jacket'
      };
    } catch (error) {
      console.error('Error getting rain forecast:', error);
      return { willRain: false, probability: 0, recommendation: 'none' };
    }
  }
}

export default WeatherService;