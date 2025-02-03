from datetime import datetime
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Movie, User, Rating
from app.schemas import MovieRecommendation, RecommendationResponse
from app.database import get_db

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from surprise import SVD, Dataset, Reader
import pandas as pd

class MovieRecommender:
    def __init__(self):
        self.content_vectorizer = TfidfVectorizer(stop_words='english')
        self.collaborative_model = SVD(n_factors=100)
        self.content_similarity_matrix = None
        self.movies_df = None
        
    def prepare_content_features(self, movies: List[Dict]) -> None:
        """Prepare content-based features using movie metadata"""
        self.movies_df = pd.DataFrame(movies)
        
        # Combine relevant features into a single text representation
        self.movies_df['content_features'] = self.movies_df.apply(
            lambda x: f"{x['title']} {x['genres']} {x['director']} {x['cast']} {x['description']}", 
            axis=1
        )
        
        # Calculate TF-IDF matrix
        tfidf_matrix = self.content_vectorizer.fit_transform(self.movies_df['content_features'])
        self.content_similarity_matrix = cosine_similarity(tfidf_matrix)
        
    def train_collaborative_model(self, ratings: List[Dict]) -> None:
        """Train collaborative filtering model using user ratings"""
        ratings_df = pd.DataFrame(ratings)
        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(ratings_df[['user_id', 'movie_id', 'rating']], reader)
        
        # Train the SVD model
        trainset = data.build_full_trainset()
        self.collaborative_model.fit(trainset)
        
    def get_content_based_recommendations(self, movie_id: int, n_recommendations: int = 10) -> List[int]:
        """Get movie recommendations based on content similarity"""
        movie_idx = self.movies_df[self.movies_df['id'] == movie_id].index[0]
        movie_similarities = self.content_similarity_matrix[movie_idx]
        
        similar_movie_indices = np.argsort(movie_similarities)[::-1][1:n_recommendations+1]
        return self.movies_df.iloc[similar_movie_indices]['id'].tolist()
        
    def get_collaborative_recommendations(self, user_id: int, n_recommendations: int = 10) -> List[tuple]:
        """Get movie recommendations based on collaborative filtering"""
        # Get all movies not rated by the user
        user_unrated = self.movies_df[~self.movies_df['id'].isin(
            self.ratings_df[self.ratings_df['user_id'] == user_id]['movie_id']
        )]
        
        # Predict ratings for unrated movies
        predictions = [
            (movie_id, self.collaborative_model.predict(user_id, movie_id).est)
            for movie_id in user_unrated['id']
        ]
        
        # Sort by predicted rating
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:n_recommendations]
        
    def get_hybrid_recommendations(
        self, 
        user_id: int, 
        recently_viewed: List[int],
        n_recommendations: int = 10
    ) -> List[int]:
        """Combine content-based and collaborative filtering recommendations"""
        # Get content-based recommendations from recently viewed movies
        content_recs = []
        for movie_id in recently_viewed[-3:]:  # Use last 3 viewed movies
            content_recs.extend(self.get_content_based_recommendations(movie_id, n_recommendations//2))
            
        # Get collaborative filtering recommendations
        collab_recs = [
            movie_id for movie_id, _ in self.get_collaborative_recommendations(user_id, n_recommendations//2)
        ]
        
        # Combine and deduplicate recommendations
        hybrid_recs = []
        seen_movies = set(recently_viewed)
        
        # Alternate between recommendation sources
        content_idx, collab_idx = 0, 0
        while len(hybrid_recs) < n_recommendations and (content_idx < len(content_recs) or collab_idx < len(collab_recs)):
            if content_idx < len(content_recs):
                movie_id = content_recs[content_idx]
                if movie_id not in seen_movies:
                    hybrid_recs.append(movie_id)
                    seen_movies.add(movie_id)
                content_idx += 1
                
            if collab_idx < len(collab_recs):
                movie_id = collab_recs[collab_idx]
                if movie_id not in seen_movies:
                    hybrid_recs.append(movie_id)
                    seen_movies.add(movie_id)
                collab_idx += 1
                
        return hybrid_recs

# FastAPI Router implementation
router = APIRouter()
recommender = MovieRecommender()

@router.post("/train")
async def train_recommender(db: Session = Depends(get_db)):
    """Train the recommendation models with current database data"""
    # Fetch movies and prepare content features
    movies = db.query(Movie).all()
    movies_data = [
        {
            "id": m.id,
            "title": m.title,
            "genres": m.genres,
            "director": m.director,
            "cast": m.cast,
            "description": m.description
        } for m in movies
    ]
    recommender.prepare_content_features(movies_data)
    
    # Fetch ratings and train collaborative model
    ratings = db.query(models.UserMovieRating).all()
    ratings_data = [
        {
            "user_id": r.user_id,
            "movie_id": r.movie_id,
            "rating": r.rating
        } for r in ratings
    ]
    recommender.train_collaborative_model(ratings_data)
    
    return {"message": "Recommendation models trained successfully"}

@router.get("/recommendations/{user_id}", response_model=RecommendationResponse)
async def get_recommendations(
    user_id: int,
    strategy: str = "hybrid",
    exclude_watched: bool = True,
    db: Session = Depends(get_db)
) -> RecommendationResponse:
    """Get personalized movie recommendations for a user"""
    # Get user's recently viewed movies
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get recent ratings, handling case where user hasn't rated anything
    recently_viewed = [r.movie_id for r in user.user_ratings][-10:] if user.user_ratings else []
    
    # If user has no ratings, return popular or trending movies instead
    if not recently_viewed:
        recommended_movies = (
            db.query(Movie)
            .order_by(Movie.average_rating.desc(), Movie.view_count.desc())
            .limit(10)
            .all()
        )
        recommendations = [
            MovieRecommendation(
                movie_id=movie.id,
                title=movie.title,
                confidence_score=0.9 - (0.05 * i),  # Descending confidence score
                recommendation_type="trending",
                reason="Popular highly-rated movie"
            )
            for i, movie in enumerate(recommended_movies)
        ]
        return RecommendationResponse(
            recommendations=recommendations,
            generated_at=datetime.now()
        )

    # Get hybrid recommendations
    recommended_ids = recommender.get_hybrid_recommendations(user_id, recently_viewed)
    
    # Fetch full movie details for recommendations
    recommended_movies = (
        db.query(Movie)
        .filter(Movie.id.in_(recommended_ids))
        .all()
    )
    
    # Sort movies in the same order as recommendations
    id_to_movie = {m.id: m for m in recommended_movies}
    recommendations = [
        MovieRecommendation(
            movie_id=movie_id,
            title=id_to_movie[movie_id].title,
            confidence_score=0.9 - 0.05 * idx,
            recommendation_type=strategy,
            reason=f"Based on your viewing history and preferences"
        )
        for idx, movie_id in enumerate(recommended_ids)
        if movie_id in id_to_movie
    ]

    return RecommendationResponse(
        recommendations=recommendations,
        generated_at=datetime.now(),
        metadata={
            "strategy": strategy,
            "user_id": user_id,
            "based_on_movies": len(recently_viewed)
        }
    )