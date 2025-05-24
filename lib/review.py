# lib/review.py
from __init__ import CURSOR, CONN
from employee import Employee  # For employee_id validation

class Review:
    """Models annual performance reviews for employees"""
    
    all = {}  # Cache for persisted instances

    def __init__(self, year, summary, employee_id, id=None):
        self.id = id
        self.year = year      # Uses @year.setter
        self.summary = summary  # Uses @summary.setter
        self.employee_id = employee_id  # Uses @employee_id.setter

    def __repr__(self):
        return f"<Review {self.id}: {self.year}, {self.summary}, Employee ID: {self.employee_id}>"

    # ----- PROPERTY VALIDATIONS -----
    @property
    def year(self):
        return self._year
    
    @year.setter
    def year(self, year):
        """Year must be integer >= 2000"""
        if isinstance(year, int) and year >= 2000:
            self._year = year
        else:
            raise ValueError("Year must be integer >= 2000")

    @property
    def summary(self):
        return self._summary
    
    @summary.setter
    def summary(self, summary):
        """Summary must be non-empty string"""
        if isinstance(summary, str) and len(summary.strip()) > 0:
            self._summary = summary
        else:
            raise ValueError("Summary must be non-empty string")

    @property
    def employee_id(self):
        return self._employee_id
    
    @employee_id.setter
    def employee_id(self, employee_id):
        """Must reference valid Employee ID"""
        if isinstance(employee_id, int) and Employee.find_by_id(employee_id):
            self._employee_id = employee_id
        else:
            raise ValueError("employee_id must reference existing Employee")

    # ----- ORM METHODS -----
    @classmethod
    def create_table(cls):
        """Create reviews table with proper foreign key"""
        sql = """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY,
                year INTEGER,
                summary TEXT,
                employee_id INTEGER,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        """
        CURSOR.execute(sql)
        CONN.commit()

    @classmethod
    def drop_table(cls):
        """Drop reviews table"""
        CURSOR.execute("DROP TABLE IF EXISTS reviews")
        CONN.commit()

    def save(self):
        """Persist instance to database"""
        sql = """
            INSERT INTO reviews (year, summary, employee_id)
            VALUES (?, ?, ?)
        """
        CURSOR.execute(sql, (self.year, self.summary, self.employee_id))
        CONN.commit()
        self.id = CURSOR.lastrowid
        type(self).all[self.id] = self  # Cache instance

    @classmethod
    def create(cls, year, summary, employee_id):
        """Create and save new Review instance"""
        review = cls(year, summary, employee_id)
        review.save()
        return review

    @classmethod
    def instance_from_db(cls, row):
        """Get cached instance or create new from DB row"""
        review = cls.all.get(row[0])
        if review:  # Update existing instance
            review.year = row[1]
            review.summary = row[2]
            review.employee_id = row[3]
        else:  # Create new instance
            review = cls(row[1], row[2], row[3])
            review.id = row[0]
            cls.all[review.id] = review
        return review

    @classmethod
    def find_by_id(cls, id):
        """Find review by ID"""
        sql = "SELECT * FROM reviews WHERE id = ?"
        row = CURSOR.execute(sql, (id,)).fetchone()
        return cls.instance_from_db(row) if row else None

    def update(self):
        """Update database row to match instance"""
        sql = """
            UPDATE reviews
            SET year = ?, summary = ?, employee_id = ?
            WHERE id = ?
        """
        CURSOR.execute(sql, (self.year, self.summary, self.employee_id, self.id))
        CONN.commit()

    def delete(self):
        """Delete database row and remove from cache"""
        sql = "DELETE FROM reviews WHERE id = ?"
        CURSOR.execute(sql, (self.id,))
        CONN.commit()
        del type(self).all[self.id]
        self.id = None

    @classmethod
    def get_all(cls):
        """Get all reviews from database"""
        sql = "SELECT * FROM reviews"
        rows = CURSOR.execute(sql).fetchall()
        return [cls.instance_from_db(row) for row in rows]